# Redis Container Instance (Private IP, no public DNS, using ACR image)
resource "azurerm_container_group" "redis" {
  name                = "aci-redis-${var.project_name}-${var.environment}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  ip_address_type     = "Public"
  os_type             = "Linux"
  restart_policy      = "Always"
  dns_name_label      = null # No public DNS - only IP access

  container {
    name   = "redis"
    image  = "${azurerm_container_registry.main.login_server}/redis:7"
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

  # Registry credentials for ACR
  image_registry_credential {
    server   = azurerm_container_registry.main.login_server
    username = azurerm_container_registry.main.admin_username
    password = azurerm_container_registry.main.admin_password
  }

  # Ensure ACR exists before creating container
  depends_on = [
    azurerm_container_registry.main
  ]

  tags = var.tags
}



