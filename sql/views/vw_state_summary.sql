-- (b) State-level average excess readmission ratio and penalty rate, over
-- reported facility-measure results. Penalty rate = share of those results
-- with a ratio above 1.0.
CREATE OR REPLACE VIEW vw_state_summary AS
SELECT d.state,
       count(DISTINCT f.facility_id) AS facilities_with_results,
       count(*) AS reported_results,
       count(*) FILTER (WHERE f.excess_readmission_ratio > 1.0) AS penalized_results,
       round(avg(f.excess_readmission_ratio), 4) AS avg_excess_ratio,
       round(count(*) FILTER (WHERE f.excess_readmission_ratio > 1.0)::numeric / count(*), 4) AS penalty_rate
FROM fact_readmission f
JOIN dim_facility d USING (facility_id)
WHERE f.is_reported
GROUP BY d.state;
