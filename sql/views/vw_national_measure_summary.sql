-- (d) National summary per measure. Suppressed results are a subset of
-- reported ones: the ratio is published but the readmission count is hidden.
CREATE OR REPLACE VIEW vw_national_measure_summary AS
SELECT m.measure_code,
       m.condition_name,
       count(*) AS facilities,
       count(*) FILTER (WHERE f.is_reported) AS reported,
       count(*) FILTER (WHERE f.is_suppressed) AS suppressed,
       count(*) FILTER (WHERE NOT f.is_reported) AS not_reported,
       round(avg(f.excess_readmission_ratio), 4) AS avg_excess_ratio,
       count(*) FILTER (WHERE f.excess_readmission_ratio > 1.0) AS penalized,
       round(count(*) FILTER (WHERE f.excess_readmission_ratio > 1.0)::numeric
             / nullif(count(*) FILTER (WHERE f.is_reported), 0), 4) AS penalty_rate
FROM fact_readmission f
JOIN dim_measure m USING (measure_id)
GROUP BY m.measure_code, m.condition_name;
