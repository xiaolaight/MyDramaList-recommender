create table cos_sim (
  row_index INT NOT NULL,
  col_index INT NOT NULL,
  sim_val DOUBLE,
  PRIMARY KEY (row_index, col_index)
);