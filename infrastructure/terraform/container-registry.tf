# Azure Container Registry
resource "azurerm_container_registry" "main" {
  name                = "acr${replace(var.project_name, "-", "")}${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = var.container_registry_sku
  admin_enabled       = true

  # Enable anonymous pull (optional - for public images)
  # anonymous_pull_enabled = false

  # Enable georeplication (Premium SKU only)
  # georeplications {
  #   location = "West US"
  #   tags     = var.tags
  # }

  tags = var.tags
}

# Grant App Service access to ACR - DEPRECATED: Using ACI instead
# ACI uses image_registry_credential instead of managed identity
# resource "azurerm_role_assignment" "acr_pull" {
#   scope                = azurerm_container_registry.main.id
#   role_definition_name = "AcrPull"
#   principal_id         = azurerm_linux_web_app.main.identity[0].principal_id
#
#   depends_on = [azurerm_linux_web_app.main]
# }


