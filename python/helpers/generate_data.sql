generate_tpch 10
copy lineitem to 'experiment_data/lineitem.csv';
copy nation to 'experiment_data/nation.csv';
copy orders to 'experiment_data/orders.csv';
copy customer to 'experiment_data/tpch_customer.csv';
copy supplier to 'experiment_data/tpch_supplier.csv';
copy part to 'experiment_data/tpch_part.csv';
copy partsupp to 'experiment_data/partsupp.csv';
copy region to 'experiment_data/region.csv';
reset
generate_tpcds 10
copy call_center to 'experiment_data/call_center.csv';
copy catalog_page to 'experiment_data/catalog_page.csv';
copy catalog_returns to 'experiment_data/catalog_returns.csv';
copy catalog_sales to 'experiment_data/catalog_sales.csv';
copy customer to 'experiment_data/customer.csv';
copy customer_address to 'experiment_data/customer_address.csv';
copy customer_demographics to 'experiment_data/customer_demographics.csv';
copy date_dim to 'experiment_data/date_dim.csv';
copy household_demographics to 'experiment_data/household_demographics.csv';
copy income_band to 'experiment_data/income_band.csv';
copy inventory to 'experiment_data/inventory.csv';
copy item to 'experiment_data/item.csv';
copy promotion to 'experiment_data/promotion.csv';
copy reason to 'experiment_data/reason.csv';
copy ship_mode to 'experiment_data/ship_mode.csv';
copy store to 'experiment_data/store.csv';
copy store_returns to 'experiment_data/store_returns.csv';
copy store_sales to 'experiment_data/store_sales.csv';
copy time_dim to 'experiment_data/time_dim.csv';
copy warehouse to 'experiment_data/warehouse.csv';
copy web_page to 'experiment_data/web_page.csv';
copy web_returns to 'experiment_data/web_returns.csv';
copy web_sales to 'experiment_data/web_sales.csv';
copy web_site to 'experiment_data/web_site.csv';
reset
generate_ssb 10
copy customer to 'experiment_data/ssb_customer.csv';
copy part to 'experiment_data/ssb_part.csv';
copy supplier  to 'experiment_data/ssb_supplier.csv';
copy "date" to 'experiment_data/date.csv';
copy lineorder to 'experiment_data/lineorder.csv';
exit
