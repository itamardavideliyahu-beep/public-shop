# This file serves as the main entry point for Terraform
# All resources are defined in separate files for better organization

# Local values for resource naming
locals {
  resource_prefix = "${var.project_name}-${var.environment}"

  common_tags = merge(
    var.tags,
    {
      Environment = var.environment
      Project     = var.project_name
    }
  )

  # Redis URL for Container Instance (with password from Key Vault)
  redis_protocol = var.redis_use_ssl ? "rediss" : "redis"
  redis_host_ip  = var.deploy_database_containers ? azurerm_container_group.redis[0].ip_address : var.redis_host
  # Password will be injected via app_settings REDIS_PASSWORD, URL constructed in app
  # URL encode the password to handle special characters
  redis_url = "${local.redis_protocol}://:${urlencode(random_password.redis_password.result)}@${local.redis_host_ip}:${var.redis_port}/0"
}


