# PostgreSQL Container Instance (using ACR image and Azure File Share)
resource "azurerm_storage_share" "postgres_data" {
  name                 = "postgres-data"
  storage_account_name = azurerm_storage_account.main.name
  quota                = 10 # 10 GB
}

# PostgreSQL Container Instance
resource "azurerm_container_group" "postgres" {
  name                = "aci-postgres-${var.project_name}-${var.environment}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  ip_address_type     = "Public"
  os_type             = "Linux"
  restart_policy      = "Always"
  dns_name_label      = null # No public DNS - only IP access

  container {
    name   = "postgres"
    image  = "${azurerm_container_registry.main.login_server}/postgres:15-alpine"
    cpu    = "0.5"
    memory = "1.0"

    ports {
      port     = 5432
      protocol = "TCP"
    }

    # PostgreSQL environment variables
    environment_variables = {
      POSTGRES_USER     = "psqladmin"
      POSTGRES_PASSWORD = random_password.postgres_password.result
      POSTGRES_DB       = "public_shop"
    }

    # Note: Using ephemeral storage for POC. For production, use Azure Database for PostgreSQL
    # or mount Azure File Share with proper permissions
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

# Random password for PostgreSQL
resource "random_password" "postgres_password" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

# Store PostgreSQL password in Key Vault
resource "azurerm_key_vault_secret" "postgres_password" {
  name         = "postgres-password"
  value        = random_password.postgres_password.result
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault_access_policy.current_user]
}
