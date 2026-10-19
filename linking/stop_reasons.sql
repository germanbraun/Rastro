-- Por qué se detuvo cada ensayo: el motivo que escribió el sponsor (why_stopped), clasificado
-- con reglas legibles. Un ensayo puede tener varios motivos («Lack of efficacy and enrollment
-- challenges» son dos). La evidencia es el texto que coincidió con cada regla.
--
-- Antes de buscar, se sacan las negaciones de seguridad y eficacia: «not related to safety»
-- o «no safety concerns» no son un problema de seguridad. Para eficacia la regla es más
-- estrecha, para no borrar «did not meet efficacy goals», que sí es un motivo.

DROP TABLE IF EXISTS linking.stop_reason_rule;
CREATE TABLE linking.stop_reason_rule (reason_id text PRIMARY KEY, reason text, pattern text);
INSERT INTO linking.stop_reason_rule VALUES
  ('pacientes',      'No consiguieron pacientes',
   '(accru|accur|recruit|enrol|enroll|referral|(no|lack of|few|insufficient|low number of|limited) (eligible |suitable )?(patients?|subjects?|participants?)|patient (availability|population|candidates)|no patients? (enter|entered|available|was|were)|sample size|withdrawal rate|drop[- ]?out|inclusion ?rate)'),
  ('empresa',        'Decisión de la empresa',
   '(business|strategic|commercial|corporate|company|portfolio|market|sponsor(''s)? decision|decision (of|by) (the )?sponsor|sponsor (unable|withdr|terminat|discontinu|closed|stopp|halt|decided|no longer)|(by|from) (the )?sponsor|decided to discontinue|sponsor''s requirement|development of [^.;]* discontinued|(withdr|lost|loss of|lack of) (sponsor|industry)|(program|development|programme) (was |has been )?(discontinued|terminated|stopped|halted|deprioriti))'),
  ('financiamiento', 'Falta de financiamiento',
   '(fund|financ|budget|grant|resources|study support|support (was )?withdrawn)'),
  ('eficacia',       'El tratamiento no funcionó',
   '(futil|efficacy|ineffective|not effective|lack of (benefit|response|activity)|no (clinical )?benefit|not beneficial|primary (end ?point|objective)|interim analys|(continuation|stopping) (criteria|rule)|criteria for continuation)'),
  ('seguridad',      'Problemas de seguridad',
   '(safety|toxicit|adverse|death|died|fatal|risk[- /]benefit|benefit[- /]risk|side effect|serious)'),
  ('comite',         'Lo recomendó un comité independiente',
   '(dsmb|idmc|\mdmc\M|data (and )?safety monitoring|monitoring (board|committee))'),
  ('regulatorio',    'Motivo regulatorio o ético',
   '(\mfda\M|regulat|\mirb\M|ethic|clinical hold|approval|\mcpp\M|committee for the protection|\mema\M|aifa)'),
  ('investigador',   'Cambió el investigador o el centro',
   '(\mpi\M|principal investigator|investigator (left|leaving|moved|relocat|retir)|staff|institution|site (closed|closure))'),
  ('pandemia',       'La pandemia de COVID-19',
   '(covid|pandemic|coronavirus|sars-cov)'),
  ('enfoque',        'Cambió el enfoque o el tratamiento estándar',
   '(standard of care|new (study|protocol|trial)|another (treatment|study|trial|protocol)|continuation study|replaced|supersed|landscape|no longer (relevant|needed|necessary|feasible|of interest)|changed|amend|re-?design|reconsider|did not progress|not progress)'),
  ('operativo',      'Problemas operativos o de suministro',
   '(administrativ|operational|logistic|feasib|supply|supplie|manufactur|drug (availability|shortage)|device)');

DROP TABLE IF EXISTS linking.trial_stop_reason;
CREATE TABLE linking.trial_stop_reason AS
WITH stopped AS (
  SELECT nct_id, why_stopped,
         regexp_replace(regexp_replace(lower(why_stopped),
             -- «no safety concerns», «not out of concern for patient safety»: cualquier negación cerca
             '(\mno\M|\mnot\M|without|unrelated|\mnon)[^.;]{0,45}safety[^.;]*', ' ', 'g'),
             -- eficacia: solo «not related / due / driven… to efficacy», para no borrar «did not meet efficacy»
             '((not|no) (related|due|driven|associated|attributable|linked|because|based|for)|unrelated to|without (any )?)[^.;]*?efficacy[^.;]*',
             ' ', 'g') AS text
  FROM aact.studies
  WHERE overall_status IN ('TERMINATED', 'WITHDRAWN', 'SUSPENDED')
    AND coalesce(trim(why_stopped), '') <> ''
),
matched AS (
  SELECT s.nct_id, r.reason_id, r.reason, substring(s.text from r.pattern) AS matched_text
  FROM stopped s JOIN linking.stop_reason_rule r ON s.text ~ r.pattern
)
SELECT * FROM matched
UNION ALL
-- Los que ninguna regla reconoce quedan como «otro», con su texto a la vista
SELECT s.nct_id, 'otro', 'Otro motivo', NULL
FROM stopped s WHERE NOT EXISTS (SELECT 1 FROM matched m WHERE m.nct_id = s.nct_id);

CREATE INDEX ON linking.trial_stop_reason (nct_id);
