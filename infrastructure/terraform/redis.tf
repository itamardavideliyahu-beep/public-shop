# Redis Container Instance (Private IP, no public DNS, using ACR image)
resource "azurerm_container_group" "redis" {
  count = var.deploy_database_containers ? 1 : 0
  name                = "aci-redis-${var.project_name}-${var.environment}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  ip_address_type     = "Public"
  os_type             = "Linux"
  restart_policy      = "Always"
  dns_name_label      = null # No public DNS - only IP access

  container {
    name   = "redis"
    image  = "redis:7-alpine"  # Use official Docker Hub image
    cpu    = "0.25"
    memory = "0.5"

    ports {
      port     = 6379
      protocol = "TCP"
    }

    # Use Redis with password authentication
    # Password is passed directly in the command (ACI doesn't support Key Vault references)
    commands = [
      "sh",
      "-c",
      "redis-server --requirepass ${random_password.redis_password.result}"
    ]
  }

  tags = var.tags
}



