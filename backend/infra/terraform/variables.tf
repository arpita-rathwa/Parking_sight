variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-south-1"
}

variable "db_password" {
  description = "RDS database password"
  type        = string
  sensitive   = true
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.medium"
}

variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "ec2_instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.medium"
}

variable "ec2_ami" {
  description = "EC2 AMI ID"
  type        = string
  default     = "ami-0e1bed4f06a3b4637"
}

variable "ec2_key_name" {
  description = "EC2 SSH key name"
  type        = string
}

variable "s3_bucket_name" {
  description = "S3 bucket name for media storage"
  type        = string
  default     = "parksight-media-storage"
}

variable "kafka_bootstrap_servers" {
  description = "Kafka bootstrap servers"
  type        = string
  default     = "localhost:9092"
}

variable "sentry_dsn" {
  description = "Sentry DSN for error tracking"
  type        = string
  default     = ""
}
