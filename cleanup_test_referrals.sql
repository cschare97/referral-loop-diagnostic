DELETE FROM lbt_data WHERE form_id IN (SELECT id FROM transactions WHERE groupname LIKE 'DIAG-TEST:%');
DELETE FROM transactions WHERE groupname LIKE 'DIAG-TEST:%';
