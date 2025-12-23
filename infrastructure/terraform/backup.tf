# Backup and Disaster Recovery Configuration

# Enable automated backups for PostgreSQL
# Note: This is configured in database.tf but we add backup policy here

# Backup retention is already set in database.tf, but we can add:
# - Point-in-time restore capability
# - Geo-redundant backups for production

# For production, consider:
# 1. Increasing backup_retention_days to 35
# 2. Enabling geo_redundant_backup
# 3. Setting up automated backup testing

# Storage Account for manual backups and exports
resource "azurerm_storage_container" "backups" {
  name                  = "backups"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

# Lifecycle management for backup retention
resource "azurerm_storage_management_policy" "backup_lifecycle" {
  storage_account_id = azurerm_storage_account.main.id

  rule {
    name    = "backup-retention"
    enabled = true

    filters {
      prefix_match = ["backups/"]
      blob_types   = ["blockBlob"]
    }

    actions {
      base_blob {
        tier_to_cool_after_days_since_modification_greater_than    = 30
        tier_to_archive_after_days_since_modification_greater_than = 90
        delete_after_days_since_modification_greater_than          = 365
      }
    }
  }
}

# Output backup information
output "backup_storage_container" {
  value       = azurerm_storage_container.backups.name
  description = "Storage container for manual backups"
}


