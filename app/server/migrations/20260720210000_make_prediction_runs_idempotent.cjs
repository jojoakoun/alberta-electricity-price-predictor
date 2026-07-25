exports.up = (pgm) => {
  pgm.sql(`
    WITH ranked_success_runs AS (
      SELECT
        id,
        ROW_NUMBER() OVER (
          PARTITION BY generated_at
          ORDER BY id DESC
        ) AS duplicate_rank
      FROM prediction_runs
      WHERE status = 'success'
    )
    DELETE FROM prediction_runs AS run
    USING ranked_success_runs AS ranked
    WHERE run.id = ranked.id
      AND ranked.duplicate_rank > 1;
  `);

  pgm.sql(`
    CREATE UNIQUE INDEX prediction_runs_success_generated_at_unique
    ON prediction_runs (generated_at)
    WHERE status = 'success';
  `);
};

exports.down = (pgm) => {
  pgm.sql(`
    DROP INDEX IF EXISTS prediction_runs_success_generated_at_unique;
  `);
};
