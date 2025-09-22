from __future__ import annotations

"""Survive — Events repository (предпросмотр за 1 день до старта + задержка +1 день после окончания).
Rewards передаётся как плоский dict.
"""

from datetime import datetime, timezone, timedelta
from pathlib import Path
import json
import zipfile
from typing import List, Optional, Dict, Union

from fastapi import HTTPException

from sqlalchemy import select, delete, desc
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from src.events.models import (
    EventModel,
    EventRatingModel,
    EventHistoryModel,
    COMPARE_STRATEGY,
    PrizeModel,  # ← вернул импорт для фолбэка
)
from src.events.DTO import EventPublicDTO, LeaderboardEntry
from src.database.models import UserModel
from src.prizes.prizes_repository import PrizesCore


def _prepare_rewards(rew: Optional[dict]) -> Optional[dict]:
    if not rew:
        return None
    return dict(rew)


class EventRatingCore:
    """Основная бизнес-логика для работы с ивентами."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.prizes_core = PrizesCore(session)

    # ------------------------------------------------------------------
    # АРХИВАЦИЯ ВСЕХ ЗАВЕРШИВШИХСЯ ИВЕНТОВ
    # ------------------------------------------------------------------
    async def archive_expired_events(self) -> None:
        now = datetime.now(timezone.utc)

        # выберем все события, которые закончились и ещё имеют результаты
        subq = (
            select(EventRatingModel.event_id)
            .group_by(EventRatingModel.event_id)
            .subquery()
        )
        events_to_archive = (
            await self.session.execute(
                select(EventModel)
                .where(EventModel.end_date < now)
                .where(EventModel.id.in_(select(subq.c.event_id)))
            )
        ).scalars().all()

        for ev in events_to_archive:
            await self.archive_event_results(ev.id)

    # ------------------------------------------------------------------
    # ТЕКУЩИЕ СОБЫТИЯ + ПРИЗЫ (+ телефоны победителей для закрытых)
    # ------------------------------------------------------------------
    async def get_current_events_with_prizes(self) -> List[EventPublicDTO]:
        """
        Возвращаем список текущих/вчера/завтра событий.
        Если у события нет своих призов в event_prizes — временно подставляем дефолт (-1),
        чтобы не ломать фронт, пока не внедрено копирование при создании события.
        Телефоны победителей подмешиваются ТОЛЬКО для закрытых событий.
        """
        now = datetime.now(timezone.utc)
        preview_start = now + timedelta(days=1)    # показываем за 1 день до старта
        cutoff = now - timedelta(days=1)           # и ещё 1 день после конца
        await self.archive_expired_events()

        stmt = (
            select(EventModel)
            .where(
                EventModel.start_date <= preview_start,
                EventModel.end_date >= cutoff,
            )
            .options(joinedload(EventModel.prizes))
            .order_by(EventModel.id)
        )
        events = (await self.session.execute(stmt)).scalars().unique().all()

        # дефолтные призы (-1), одним запросом для избежания N+1
        default_prizes: list[PrizeModel] = (
            (await self.session.execute(select(PrizeModel).where(PrizeModel.event_id == -1)))
        ).scalars().all()

        enriched: list[EventPublicDTO] = []
        for ev in events:
            # берём {place: phone} из последнего архива и маскируем как в лидерборде
            phones_by_place: Dict[int, str] = {}
            if ev.end_date < now:
                try:
                    raw = await self._load_winner_phones(ev.id)
                    phones_by_place = {
                        place: LeaderboardEntry._mask(ph) if ph else ph
                        for place, ph in raw.items()
                    }
                except Exception:
                    phones_by_place = {}

            # локальные призы или дефолтные
            prizes = ev.prizes if ev.prizes else default_prizes

            # level_ids могут быть mixed (int|str)
            try:
                level_ids: list[Union[int, str]] = list(ev.level_ids) if ev.level_ids else []
            except Exception:
                level_ids = []

            enriched.append(
                EventPublicDTO(
                    id=ev.id,
                    name=ev.name,
                    event_type=ev.event_type,
                    logo=ev.logo,
                    start_date=ev.start_date,
                    end_date=ev.end_date,
                    level_ids=level_ids,
                    prizes=[
                        (
                            {"place": p.place, "rewards": p.rewards or {}}
                            |
                            # ВАЖНО: добавляем phone ТОЛЬКО для закрытых ивентов и ТОЛЬКО если он есть
                            (
                                (lambda ph: {"phone": ph} if (ev.end_date < now and ph) else {})(
                                    phones_by_place.get(p.place)
                                )
                            )
                        )
                        for p in (prizes or [])
                    ],
                )
            )

        return enriched

    # alias на старое имя (если где-то используется)
    get_all_active_events_with_prizes = get_current_events_with_prizes

    # ------------------------------------------------------------------
    # ДОБАВЛЕНИЕ/АККУМУЛЯЦИИ РЕЗУЛЬТАТА И ПОДСЧЁТ МЕСТА
    # ------------------------------------------------------------------
    async def submit_event_result(
        self,
        user_id: int,
        event_id: int,
        result: float,
    ) -> tuple[float, int]:
        """
        Аккумулирует результат игрока и возвращает (new_total, place).
        Стратегия места зависит от COMPARE_STRATEGY[event_type]:
          - "higher": больше — лучше;
          - "lower": меньше — лучше.
        """
        now = datetime.now(timezone.utc)

        # Берём только нужные поля, чтобы избежать MissingGreenlet
        ev_row = await self.session.execute(
            select(EventModel.event_type, EventModel.end_date).where(EventModel.id == event_id)
        )
        ev = ev_row.first()
        if not ev:
            raise HTTPException(status_code=404, detail="EVENT_NOT_FOUND")

        event_type, end_date = ev
        if end_date < now:
            raise HTTPException(status_code=501, detail="EVENT_CLOSED")

        # upsert результата
        existing = await self.session.scalar(
            select(EventRatingModel).where(
                EventRatingModel.event_id == event_id,
                EventRatingModel.user_id == user_id,
            )
        )
        if existing:
            existing.result = float(existing.result) + float(result)
            new_total = existing.result
        else:
            row = EventRatingModel(event_id=event_id, user_id=user_id, result=float(result))
            self.session.add(row)
            new_total = row.result

        await self.session.commit()

        # пересчёт места
        order_desc = COMPARE_STRATEGY.get(event_type, "higher") == "higher"
        rows = (
            await self.session.execute(
                select(EventRatingModel.user_id, EventRatingModel.result)
                .where(EventRatingModel.event_id == event_id)
                .order_by(EventRatingModel.result.desc() if order_desc else EventRatingModel.result.asc())
            )
        ).all()

        place = 1
        for idx, (uid, _res) in enumerate(rows, start=1):
            if uid == user_id:
                place = idx
                break

        return float(new_total), int(place)

    # ------------------------------------------------------------------
    #  ВНУТРЕННЕЕ: карта призов {place: rewards}
    #     — если у события нет своих призов, используем дефолт (-1)
    # ------------------------------------------------------------------
    async def _load_prizes_map(self, event_id: int) -> Dict[int, dict]:
        event: Optional[EventModel] = await self.session.scalar(
            select(EventModel)
            .where(EventModel.id == event_id)
            .options(joinedload(EventModel.prizes))
        )
        prizes: list[PrizeModel] = []
        if event and event.prizes:
            prizes = list(event.prizes)
        else:
            prizes = (
                (await self.session.execute(select(PrizeModel).where(PrizeModel.event_id == -1)))
            ).scalars().all()

        return {p.place: p.rewards for p in (prizes or []) if p.rewards}

    # ------------------------------------------------------------------
    #  ЛИДЕРБОРД (возвращаем ЧИСТЫЕ dict’ы, не pydantic-модели)
    # ------------------------------------------------------------------
    async def get_leaderboard(
        self,
        event_id: int,
        current_user_id: int | None = None,
        top_n: int = 10,
    ):
        prize_map = await self._load_prizes_map(event_id)

        ev = await self.session.scalar(select(EventModel).where(EventModel.id == event_id))
        if not ev:
            raise HTTPException(status_code=404, detail="Event not found")

        order_desc = COMPARE_STRATEGY.get(ev.event_type, "higher") == "higher"

        rows = (
            await self.session.execute(
                select(
                    EventRatingModel.user_id,
                    EventRatingModel.result,
                )
                .where(EventRatingModel.event_id == event_id)
                .order_by(EventRatingModel.result.desc() if order_desc else EventRatingModel.result.asc())
            )
        ).all()

        all_results = [{"user_id": r[0], "result": r[1]} for r in rows]

        # подтягиваем телефоны разом
        user_ids = [r["user_id"] for r in all_results]
        id_to_phone: Dict[int, Optional[str]] = {}
        if user_ids:
            rows_ph = (
                await self.session.execute(
                    select(UserModel.id, UserModel.phone).where(UserModel.id.in_(user_ids))
                )
            ).all()
            id_to_phone = {rid: ph for rid, ph in rows_ph}

        # сортировка по стратегии
        sorted_rows = sorted(all_results, key=lambda r: r["result"], reverse=order_desc)

        # top-N как список dict’ов
        top_out: List[dict] = []
        for idx, row in enumerate(sorted_rows[:top_n], start=1):
            phone = id_to_phone.get(row["user_id"])
            masked = LeaderboardEntry._mask(phone) if phone else None
            top_out.append(
                {
                    "user_id": row["user_id"],
                    "result": float(row["result"]),
                    "place": idx,
                    "rewards": _prepare_rewards(prize_map.get(idx)),
                    "user_name": masked,
                }
            )

        # позиция текущего игрока — тоже dict
        cur_out: Optional[dict] = None
        if current_user_id is not None:
            try:
                user_pos = next(i for i, r in enumerate(sorted_rows) if r["user_id"] == current_user_id)
            except StopIteration:
                cur_out = None
            else:
                phone = id_to_phone.get(current_user_id)
                masked_me = LeaderboardEntry._mask(phone) if phone else None
                cur_out = {
                    "user_id": current_user_id,
                    "result": float(sorted_rows[user_pos]["result"]),
                    "place": user_pos + 1,
                    "rewards": _prepare_rewards(prize_map.get(user_pos + 1)),
                    "user_name": masked_me,
                }

        return top_out, cur_out

    # ------------------------------------------------------------------
    #  АРХИВАЦИЯ ОДНОГО СОБЫТИЯ
    # ------------------------------------------------------------------
    async def archive_event_results(self, event_id: int) -> None:
        ev = await self.session.scalar(select(EventModel).where(EventModel.id == event_id))
        if not ev:
            return

        # 1. Собираем весь лидерборд
        rows = (
            await self.session.execute(
                select(
                    EventRatingModel.user_id,
                    EventRatingModel.result,
                ).where(EventRatingModel.event_id == event_id)
            )
        ).all()

        order_desc = COMPARE_STRATEGY.get(ev.event_type, "higher") == "higher"
        sorted_rows = sorted(rows, key=lambda r: r[1], reverse=order_desc)

        prize_map = await self._load_prizes_map(event_id)

        payload = []
        for idx, (uid, res) in enumerate(sorted_rows, start=1):
            payload.append(
                {
                    "user_id": uid,
                    "result": float(res),
                    "place": idx,
                    "rewards": _prepare_rewards(prize_map.get(idx)),
                }
            )

        # 2. Сохраняем в архив
        hist = EventHistoryModel(
            event_id=event_id,
            ended_at=datetime.now(timezone.utc),
            results=payload,
        )
        self.session.add(hist)
        await self.session.commit()

        # zip с leaderbord.json (опционально)
        archives_dir = Path("/app/archives")
        archives_dir.mkdir(parents=True, exist_ok=True)
        zip_path = archives_dir / f"event_{event_id}.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("leaderboard.json", json.dumps(payload, ensure_ascii=False))

        # 3. Непретензованные призы
        await self.prizes_core.add_unclaimed_prizes_from_archive(event_id, payload)

        # 4. Чистим активные результаты
        await self.session.execute(
            delete(EventRatingModel).where(EventRatingModel.event_id == event_id)
        )
        await self.session.commit()

    # ------------------------------------------------------------------
    #  ВНУТРЕННЕЕ: телефоны победителей по местам из архива
    # ------------------------------------------------------------------
    async def _load_winner_phones(self, event_id: int) -> Dict[int, str]:
        """Возвращает {place: phone} для последнего архива этого события."""
        hist = await self.session.scalar(
            select(EventHistoryModel)
            .where(EventHistoryModel.event_id == event_id)
            .order_by(desc(EventHistoryModel.ended_at))
        )
        if not hist or not hist.results:
            return {}

        # place -> user_id (берём первый встретившийся)
        place_to_user: Dict[int, int] = {}
        for row in hist.results:
            try:
                place = int(row.get("place"))
                uid = int(row.get("user_id"))
            except Exception:
                continue
            place_to_user.setdefault(place, uid)

        if not place_to_user:
            return {}

        user_ids = list({uid for uid in place_to_user.values() if isinstance(uid, int)})
        if not user_ids:
            return {}

        rows = (
            await self.session.execute(
                select(UserModel.id, UserModel.phone).where(UserModel.id.in_(user_ids))
            )
        ).all()

        id_to_phone = {rid: ph for rid, ph in rows if ph}
        phones_by_place: Dict[int, str] = {}
        for place, uid in place_to_user.items():
            ph = id_to_phone.get(uid)
            if ph:
                phones_by_place[place] = ph
        return phones_by_place
