output "rds_endpoint" {
  value = aws_db_instance.postgres.address
}

output "redis_endpoint" {
  value = aws_elasticache_cluster.redis.cache_nodes[0].address
}

output "backend_public_ip" {
  value = aws_instance.backend_host.public_ip
}

output "s3_bucket_name" {
  value = aws_s3_bucket.media_bucket.id
}

output "cloudfront_domain" {
  value = aws_cloudfront_distribution.cdn.domain_name
}
