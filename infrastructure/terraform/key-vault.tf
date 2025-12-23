# Key Vault for storing secrets
resource "azurerm_key_vault" "main" {
  name                = "kv-${var.project_name}-${var.environment}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"

  # Network ACLs - allow access from Azure services (ACI doesn't need special access)
  network_acls {
    default_action = "Allow"
    bypass         = "AzureServices"
  }

  # Enable soft delete and purge protection
  soft_delete_retention_days = 7
  purge_protection_enabled   = false # Set to true in production for extra security

  tags = var.tags
}

# Get current Azure client config
data "azurerm_client_config" "current" {}

# Access policy for current user (to create secrets)
resource "azurerm_key_vault_access_policy" "current_user" {
  key_vault_id = azurerm_key_vault.main.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = data.azurerm_client_config.current.object_id

  secret_permissions = [
    "Get",
    "List",
    "Set",
    "Delete",
    "Recover",
    "Backup",
    "Restore",
  ]
}

# Access policy for App Service managed identity - DEPRECATED: Using ACI instead
# ACI doesn't support managed identity, so secrets are passed via environment variables
# resource "azurerm_key_vault_access_policy" "app_service" {
#   key_vault_id = azurerm_key_vault.main.id
#   tenant_id    = data.azurerm_client_config.current.tenant_id
#   object_id    = azurerm_linux_web_app.main.identity[0].principal_id
#
#   secret_permissions = [
#     "Get",
#     "List",
#   ]
#
#   # Create access policy after app service is created
#   depends_on = [azurerm_linux_web_app.main]
# }

# Secret for Flask SECRET_KEY
resource "azurerm_key_vault_secret" "secret_key" {
  name         = "flask-secret-key"
  value        = random_password.flask_secret_key.result
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault_access_policy.current_user]
}

# Random password for Flask SECRET_KEY
resource "random_password" "flask_secret_key" {
  length  = 64
  special = true
}

# Random password for Redis
resource "random_password" "redis_password" {
  length  = 32
  special = true
}

# Secret for Redis password
resource "azurerm_key_vault_secret" "redis_password" {
  name         = "redis-password"
  value        = random_password.redis_password.result
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault_access_policy.current_user]
}

# Email credentials in Key Vault
resource "azurerm_key_vault_secret" "mail_username" {
  name         = "mail-username"
  value        = var.mail_username
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault_access_policy.current_user]
}

resource "azurerm_key_vault_secret" "mail_password" {
  name         = "mail-password"
  value        = var.mail_password
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault_access_policy.current_user]
}

