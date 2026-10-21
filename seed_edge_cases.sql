-- Edge-case test referrals. Tagged DIAG-TEST:<expected>; cleanup_test_referrals.sql removes them too.

INSERT INTO transactions (date, title, pid, user, groupname, authorized) VALUES ('2026-10-05 09:00:00', 'LBTref', (SELECT pid FROM patient_data ORDER BY pid LIMIT 1 OFFSET 0), 'admin', 'DIAG-TEST:date_problem', 1);
SET @tid = LAST_INSERT_ID();
INSERT INTO lbt_data (form_id, field_id, field_value) VALUES (@tid, 'refer_date', '10/05/2026'), (@tid, 'refer_to', 'Cardiology'), (@tid, 'refer_from', 'admin'), (@tid, 'body', 'Evaluate and treat'), (@tid, 'refer_diag', 'R99');

INSERT INTO transactions (date, title, pid, user, groupname, authorized) VALUES ('2026-09-10 09:00:00', 'LBTref', (SELECT pid FROM patient_data ORDER BY pid LIMIT 1 OFFSET 1), 'admin', 'DIAG-TEST:date_problem', 1);
SET @tid = LAST_INSERT_ID();
INSERT INTO lbt_data (form_id, field_id, field_value) VALUES (@tid, 'refer_date', '2026-09-10'), (@tid, 'refer_to', 'Cardiology'), (@tid, 'refer_from', 'admin'), (@tid, 'body', 'Evaluate and treat'), (@tid, 'refer_diag', 'R99'), (@tid, 'reply_date', '2026-08-01'), (@tid, 'reply_findings', 'Seen');

INSERT INTO transactions (date, title, pid, user, groupname, authorized) VALUES ('2026-12-01 09:00:00', 'LBTref', (SELECT pid FROM patient_data ORDER BY pid LIMIT 1 OFFSET 2), 'admin', 'DIAG-TEST:date_problem', 1);
SET @tid = LAST_INSERT_ID();
INSERT INTO lbt_data (form_id, field_id, field_value) VALUES (@tid, 'refer_date', '2026-12-01'), (@tid, 'refer_to', 'Cardiology'), (@tid, 'refer_from', 'admin'), (@tid, 'body', 'Evaluate and treat'), (@tid, 'refer_diag', 'R99');

INSERT INTO transactions (date, title, pid, user, groupname, authorized) VALUES ('2026-08-15 09:00:00', 'LBTref', (SELECT pid FROM patient_data ORDER BY pid LIMIT 1 OFFSET 3), 'admin', 'DIAG-TEST:reply_empty', 1);
SET @tid = LAST_INSERT_ID();
INSERT INTO lbt_data (form_id, field_id, field_value) VALUES (@tid, 'refer_date', '2026-08-15'), (@tid, 'refer_to', 'Cardiology'), (@tid, 'refer_from', 'admin'), (@tid, 'body', 'Evaluate and treat'), (@tid, 'refer_diag', 'R99'), (@tid, 'reply_date', '2026-09-05'), (@tid, 'reply_findings', '');

INSERT INTO transactions (date, title, pid, user, groupname, authorized) VALUES ('2026-07-20 09:00:00', 'LBTref', (SELECT pid FROM patient_data ORDER BY pid LIMIT 1 OFFSET 4), 'admin', 'DIAG-TEST:missing_data', 1);
SET @tid = LAST_INSERT_ID();
INSERT INTO lbt_data (form_id, field_id, field_value) VALUES (@tid, 'refer_date', '2026-07-20'), (@tid, 'refer_to', 'Cardiology'), (@tid, 'refer_from', 'admin'), (@tid, 'body', ''), (@tid, 'refer_diag', '');

INSERT INTO transactions (date, title, pid, user, groupname, authorized) VALUES ('2026-08-20 09:00:00', 'LBTref', (SELECT pid FROM patient_data ORDER BY pid LIMIT 1 OFFSET 0), 'admin', 'DIAG-TEST:missing_data', 1);
SET @tid = LAST_INSERT_ID();
INSERT INTO lbt_data (form_id, field_id, field_value) VALUES (@tid, 'refer_date', '2026-08-20'), (@tid, 'refer_to', 'Cardiology'), (@tid, 'refer_from', 'admin'), (@tid, 'body', '   '), (@tid, 'refer_diag', 'R99');

INSERT INTO transactions (date, title, pid, user, groupname, authorized) VALUES (NOW(), 'LBTref', (SELECT pid FROM patient_data ORDER BY pid LIMIT 1 OFFSET 1), 'admin', 'DIAG-TEST:missing_data', 1);
SET @tid = LAST_INSERT_ID();

INSERT INTO transactions (date, title, pid, user, groupname, authorized) VALUES ('2026-09-20 09:00:00', 'LBTref', (SELECT pid FROM patient_data ORDER BY pid LIMIT 1 OFFSET 2), 'admin', 'DIAG-TEST:in_progress', 1);
SET @tid = LAST_INSERT_ID();
INSERT INTO lbt_data (form_id, field_id, field_value) VALUES (@tid, 'refer_date', '2026-09-20'), (@tid, 'refer_to', 'Cardiology'), (@tid, 'refer_from', 'admin'), (@tid, 'body', 'Evaluate and treat'), (@tid, 'refer_diag', 'R99');

INSERT INTO transactions (date, title, pid, user, groupname, authorized) VALUES ('2026-09-19 09:00:00', 'LBTref', (SELECT pid FROM patient_data ORDER BY pid LIMIT 1 OFFSET 3), 'admin', 'DIAG-TEST:no_reply', 1);
SET @tid = LAST_INSERT_ID();
INSERT INTO lbt_data (form_id, field_id, field_value) VALUES (@tid, 'refer_date', '2026-09-19'), (@tid, 'refer_to', 'Cardiology'), (@tid, 'refer_from', 'admin'), (@tid, 'body', 'Evaluate and treat'), (@tid, 'refer_diag', 'R99');

INSERT INTO transactions (date, title, pid, user, groupname, authorized) VALUES ('2026-07-01 09:00:00', 'LBTref', (SELECT pid FROM patient_data ORDER BY pid LIMIT 1 OFFSET 4), 'admin', 'DIAG-TEST:no_reply', 1);
SET @tid = LAST_INSERT_ID();
INSERT INTO lbt_data (form_id, field_id, field_value) VALUES (@tid, 'refer_date', '2026-07-01'), (@tid, 'refer_to', 'Cardiology'), (@tid, 'refer_from', 'admin'), (@tid, 'body', 'Evaluate and treat'), (@tid, 'refer_diag', 'R99');

INSERT INTO transactions (date, title, pid, user, groupname, authorized) VALUES ('2026-07-02 09:00:00', 'LBTref', (SELECT pid FROM patient_data ORDER BY pid LIMIT 1 OFFSET 4), 'admin', 'DIAG-TEST:closed', 1);
SET @tid = LAST_INSERT_ID();
INSERT INTO lbt_data (form_id, field_id, field_value) VALUES (@tid, 'refer_date', '2026-07-02'), (@tid, 'refer_to', 'Cardiology'), (@tid, 'refer_from', 'admin'), (@tid, 'body', 'Evaluate and treat'), (@tid, 'refer_diag', 'R99'), (@tid, 'reply_date', '2026-07-20'), (@tid, 'reply_findings', 'Seen and assessed');
