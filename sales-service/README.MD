
Sales Service

    Sales service is a microservice built on Python using FastAPI.

APIS

   * Create sale — POST /sales/
     Accepts sale_id, customer_name, sale_datetime, created_by, and a list of items (item_id, item_name, sales_item_qty).
     Stores the sale in the sales table (sale_id, customer_name, sale_datetime, status, created_date, updated_date, created_by, updated_by)
     and each item in the salesdetails table (item_id, sale_id, item_name, sales_item_qty, created_date, updated_date, created_by, updated_by).
     Sale is created with status = "pending".

   * Update sale — PUT /sales/{sale_id}
     Accepts customer_name, sale_datetime, updated_by, and an optional updated list of items.
     Updates the sales table and replaces salesdetails rows if items are provided.

   * Delete sale — DELETE /sales/{sale_id}
     Accepts the sale_id. Deletes the record from both the sales and salesdetails tables.

   * List sales — GET /sales/
     Returns sale_id, customer_name, and sale_datetime with pagination (page, page_size).

   * Get sale — GET /sales/{sale_id}
     Returns the full sale record including all items, status, approved_date, and approved_by.

   * Approve sale — POST /sales/{sale_id}/approve
     Accepts approved_by (optional, defaults to "system").
     Fetches the sale and validates it exists and is not already approved.
     Calls the stock service (STOCK_SERVICE_URL, default http://localhost:8000) bulk reduce endpoint
     (PATCH /stocks/bulk/reduce) to reduce stock qty for each item in the sale.
     If any item fails stock reduction (not found or insufficient qty) the approval is rejected with a 400 error.
     On success, marks the sale status as "approved" and records approved_date, approved_by, updated_date, and updated_by.
     Returns 400 if the sale is already approved.
     Returns 502 if the stock service is unreachable or returns an error.

CONFIGURATION

   * STOCK_SERVICE_URL — URL of the stock service (default: http://localhost:8000)
