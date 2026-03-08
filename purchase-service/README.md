
purchase Service 
 
     purchase service is microservice which is build on python using fast api 

APIS

   * Create purchase, it acccept the purchase id, vendor name, purchase date time, and it get stored in the backend table with purchase id , vendor name, purchase date time, created date, updated date, created by, and updated by. 
     purchase item id, item name and purchase qty get stored in purchasedetails table wih purchase id, item id,  item name, purchase item qty, created date, updated date, created by and updated by

  * update purchase, it acccept the purchase id, vendor name, purchase date time, and it get stored in the backend table with purchase id , vendor name, purchase date time, created date, updated date, created by, and updated by. 
     purchase item id, item name and purchase qty get stored in purchasedetails table wih purchase id, item id,  item name, purchase item qty, created date, updated date, created by and updated by

   * delete the purchase, it accept the purchase id, it delete the data from purchase and purchasedetails back end table

   * list the purchase, purchase id, vendor name and purchase date time with pagingnation

   * approve purchase, it accepts the purchase id, it fetches the purchase details and for each item in the purchase
     it calls the stock service to add the stock. the stock service is assumed to be running on port 8000.
     if the purchase is already approved it returns an error. on success it marks the purchase status as approved
     with the approved date, approved by, and updates the updated date and updated by fields in the purchase table.