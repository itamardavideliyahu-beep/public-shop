output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "resource_group_location" {
  description = "Location of the resource group"
  value       = azurerm_resource_group.main.location
}

output "app_container_name" {
  description = "Name of the App Container Instance"
  value       = azurerm_container_group.app.name
}

output "app_container_ip" {
  description = "IP address of the App Container Instance"
  value       = azurerm_container_group.app.ip_address
}

output "app_container_fqdn" {
  description = "FQDN of the App Container Instance"
  value       = azurerm_container_group.app.fqdn
}

output "app_service_url" {
  description = "URL of the App Container Instance"
  value       = "http://${azurerm_container_group.app.fqdn}:8000"
}

output "postgresql_container_name" {
  description = "Name of the PostgreSQL container instance"
  value       = azurerm_container_group.postgres.name
}

output "postgresql_container_ip" {
  description = "IP address of the PostgreSQL container instance"
  value       = azurerm_container_group.postgres.ip_address
}

output "postgresql_database_name" {
  description = "Name of the PostgreSQL database"
  value       = "public_shop"
}

output "container_registry_name" {
  description = "Name of the Container Registry"
  value       = azurerm_container_registry.main.name
}

output "container_registry_login_server" {
  description = "Login server of the Container Registry"
  value       = azurerm_container_registry.main.login_server
}

output "storage_account_name" {
  description = "Name of the Storage Account"
  value       = azurerm_storage_account.main.name
}

output "storage_account_primary_blob_endpoint" {
  description = "Primary blob endpoint of the Storage Account"
  value       = azurerm_storage_account.main.primary_blob_endpoint
}

output "key_vault_name" {
  description = "Name of the Key Vault"
  value       = azurerm_key_vault.main.name
}

output "key_vault_uri" {
  description = "URI of the Key Vault"
  value       = azurerm_key_vault.main.vault_uri
}

output "application_insights_instrumentation_key" {
  description = "Instrumentation key for Application Insights"
  value       = azurerm_application_insights.main.instrumentation_key
  sensitive   = true
}

output "application_insights_connection_string" {
  description = "Connection string for Application Insights"
  value       = azurerm_application_insights.main.connection_string
  sensitive   = true
}

# App Service identity - DEPRECATED: Using ACI instead
# output "app_service_identity_principal_id" {
#   description = "Principal ID of the App Service managed identity"
#   value       = azurerm_linux_web_app.main.identity[0].principal_id
# }

output "redis_container_ip" {
  description = "IP address of the Redis container instance"
  value       = azurerm_container_group.redis.ip_address
}

output "redis_container_fqdn" {
  description = "FQDN of the Redis container instance (null if no DNS label)"
  value       = try(azurerm_container_group.redis.fqdn, null)
}

output "redis_container_name" {
  description = "Name of the Redis container instance"
  value       = azurerm_container_group.redis.name
}

