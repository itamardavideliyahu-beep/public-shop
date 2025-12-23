# Storage Account for file uploads
resource "azurerm_storage_account" "main" {
  name                     = "st${replace(var.project_name, "-", "")}${var.environment}"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = var.storage_account_tier
  account_replication_type = var.storage_account_replication_type
  min_tls_version          = "TLS1_2"

  # Enable blob versioning and soft delete
  blob_properties {
    versioning_enabled = true
    delete_retention_policy {
      days = 30
    }
    container_delete_retention_policy {
      days = 30
    }
  }

  tags = var.tags
}

# Container for avatars
resource "azurerm_storage_container" "avatars" {
  name                  = "avatars"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

# Container for listings
resource "azurerm_storage_container" "listings" {
  name                  = "listings"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

# Optional: Storage Account for static website hosting (if needed)
# resource "azurerm_storage_account" "static" {
#   name                     = "st${replace(var.project_name, "-", "")}static${var.environment}"
#   resource_group_name      = azurerm_resource_group.main.name
#   location                 = azurerm_resource_group.main.location
#   account_tier             = "Standard"
#   account_replication_type = "LRS"
#   account_kind             = "StorageV2"
#   
#   static_website {
#     index_document     = "index.html"
#     error_404_document = "404.html"
#   }
# }






