
Build Infra 

    Build infra in aws using terraform 

Networks

    * Create one vpc in ap-south-1, which has 3 public subnet, 3 private subnet, and 3 private subnet
    * by default all nsg rules is allowed, and configured the route table
    * Create a regional nat gateway in public subnet and internet gateway 
    * Create a eks in cluster in private subnet, with endpoint access both public and private 
    * with one nodepool and instance type t3.micro
