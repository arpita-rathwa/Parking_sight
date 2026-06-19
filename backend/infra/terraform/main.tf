provider "aws" {
  region = var.aws_region
}

resource "aws_vpc" "parksight_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = { Name = "parksight-vpc" }
}

resource "aws_subnet" "public_subnet_a" {
  vpc_id            = aws_vpc.parksight_vpc.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "${var.aws_region}a"
  map_public_ip_on_launch = true
  tags = { Name = "parksight-public-a" }
}

resource "aws_subnet" "public_subnet_b" {
  vpc_id            = aws_vpc.parksight_vpc.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "${var.aws_region}b"
  map_public_ip_on_launch = true
  tags = { Name = "parksight-public-b" }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.parksight_vpc.id
  tags = { Name = "parksight-igw" }
}

resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.parksight_vpc.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
  tags = { Name = "parksight-public-rt" }
}

resource "aws_route_table_association" "public_a" {
  subnet_id      = aws_subnet.public_subnet_a.id
  route_table_id = aws_route_table.public_rt.id
}

resource "aws_route_table_association" "public_b" {
  subnet_id      = aws_subnet.public_subnet_b.id
  route_table_id = aws_route_table.public_rt.id
}

resource "aws_security_group" "backend_sg" {
  name        = "parksight-backend-sg"
  description = "Security group for ParkSight backend services"
  vpc_id      = aws_vpc.parksight_vpc.id

  ingress {
    from_port   = 8000
    to_port     = 8006
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }
  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }
  ingress {
    from_port   = 9092
    to_port     = 9092
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = { Name = "parksight-backend-sg" }
}

resource "aws_db_instance" "postgres" {
  identifier        = "parksight-db"
  engine            = "postgres"
  engine_version    = "16.3"
  instance_class    = var.db_instance_class
  allocated_storage = 20
  db_name           = "parksight"
  username          = "parksight"
  password          = var.db_password
  skip_final_snapshot = true
  publicly_accessible = false
  vpc_security_group_ids = [aws_security_group.backend_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.parksight_subnet_group.name
  tags = { Name = "parksight-rds" }
}

resource "aws_db_subnet_group" "parksight_subnet_group" {
  name       = "parksight-db-subnet-group"
  subnet_ids = [aws_subnet.public_subnet_a.id, aws_subnet.public_subnet_b.id]
}

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "parksight-redis"
  engine               = "redis"
  node_type            = var.redis_node_type
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  security_group_ids   = [aws_security_group.backend_sg.id]
  subnet_group_name    = aws_elasticache_subnet_group.redis_subnet_group.name
  tags = { Name = "parksight-redis" }
}

resource "aws_elasticache_subnet_group" "redis_subnet_group" {
  name       = "parksight-redis-subnet-group"
  subnet_ids = [aws_subnet.public_subnet_a.id, aws_subnet.public_subnet_b.id]
}

resource "aws_s3_bucket" "media_bucket" {
  bucket = var.s3_bucket_name
  tags = { Name = "parksight-media" }
}

resource "aws_s3_bucket_public_access_block" "media_block" {
  bucket = aws_s3_bucket.media_bucket.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_cloudfront_distribution" "cdn" {
  enabled = true
  origin {
    domain_name = aws_s3_bucket.media_bucket.bucket_regional_domain_name
    origin_id   = "parksight-media"
  }
  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "parksight-media"
    viewer_protocol_policy = "redirect-to-https"
    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
    min_ttl     = 0
    default_ttl = 86400
    max_ttl     = 31536000
  }
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }
  viewer_certificate {
    cloudfront_default_certificate = true
  }
  tags = { Name = "parksight-cdn" }
}

resource "aws_instance" "backend_host" {
  ami                    = var.ec2_ami
  instance_type          = var.ec2_instance_type
  subnet_id              = aws_subnet.public_subnet_a.id
  vpc_security_group_ids = [aws_security_group.backend_sg.id]
  key_name               = var.ec2_key_name
  user_data              = templatefile("${path.module}/user_data.sh", {
    db_url      = "postgresql+psycopg2://parksight:${var.db_password}@${aws_db_instance.postgres.address}:5432/parksight"
    redis_url   = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:6379/0"
    kafka_servers = var.kafka_bootstrap_servers
    sentry_dsn  = var.sentry_dsn
  })
  tags = { Name = "parksight-backend-host" }
}
