variable "region" {
  description = "AWS region"
  type        = string
  default     = "ap-south-1"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets (one per AZ)"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets - app tier (one per AZ)"
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24", "10.0.13.0/24"]
}

variable "isolated_subnet_cidrs" {
  description = "CIDR blocks for isolated private subnets - db tier (one per AZ)"
  type        = list(string)
  default     = ["10.0.21.0/24", "10.0.22.0/24", "10.0.23.0/24"]
}

variable "availability_zones" {
  description = "Availability zones in ap-south-1"
  type        = list(string)
  default     = ["ap-south-1a", "ap-south-1b", "ap-south-1c"]
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "inventory-mgmt-cluster"
}

variable "eks_node_instance_type" {
  description = "EC2 instance type for EKS nodes"
  type        = string
  default     = "t3.micro"
}

variable "eks_desired_nodes" {
  description = "Desired number of nodes in the node group"
  type        = number
  default     = 2
}

variable "eks_min_nodes" {
  description = "Minimum number of nodes in the node group"
  type        = number
  default     = 1
}

variable "eks_max_nodes" {
  description = "Maximum number of nodes in the node group"
  type        = number
  default     = 3
}
