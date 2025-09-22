Из-под хоста (не заходя внутрь контейнера)	
`bash\ndocker exec -it postgres_survive psql -U myuser -d mydatabase\n`

в контейнере 
`psql -U myuser -d mydatabase`


1. Пользователь 
```
WITH new_user AS (
  INSERT INTO users
    (phone, gold, skin, wood, stone, grass, berry, brick, fish, boards, rope)
  VALUES ('+79991234567', 1000, 'default_skin',
          500, 500, 500, 100, 100, 50, 20, 0)
  RETURNING id
),
```
2.
```ins_token AS (
  INSERT INTO tokens (id_user, token, expires_at)
  SELECT id,
         '393e0c78db209ceb2cd24690fa5d8542a6da6f96',
         now() + interval '7 days'
  FROM new_user
)
```

3. 
```INSERT INTO events
  (name, event_type, start_date, end_date, level_ids)
VALUES ('Test Event', 'TST',
        now() - interval '1 hour',
        now() + interval '1 hour',
        ARRAY[1,2,3]);```
 


