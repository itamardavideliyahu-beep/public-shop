# Security Best Practices Configuration

# Network Security Group for database
resource "azurerm_network_security_group" "database" {
  name                = "${local.resource_prefix}-db-nsg"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  # Allow PostgreSQL from app subnet only
  security_rule {
    name                       = "AllowPostgreSQL"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "5432"
    source_address_prefix      = "VirtualNetwork"
    destination_address_prefix = "*"
  }

  # Deny all other inbound traffic
  security_rule {
    name                       = "DenyAllInbound"
    priority                   = 4096
    direction                  = "Inbound"
    access                     = "Deny"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  tags = local.common_tags
}

# Key Vault access policies - restrict to specific identities
# Already configured in key-vault.tf, but ensuring best practices

# Ensure SSL/TLS is enforced for PostgreSQL
# Already configured in database.tf with minimum TLS version

# Storage account security settings
resource "azurerm_storage_account_network_rules" "main" {
  storage_account_id = azurerm_storage_account.main.id

  default_action             = "Allow"  # Changed to Allow for POC - use "Deny" with specific IP rules for production
  ip_rules                   = var.allowed_ip_addresses
  virtual_network_subnet_ids = []
  bypass                     = ["AzureServices"]
}

# Enable Azure Defender for resources (Optional - requires additional cost)
# Uncomment for production environments

# resource "azurerm_security_center_subscription_pricing" "databases" {
#   tier          = "Standard"
#   resource_type = "SqlServers"
# }

# resource "azurerm_security_center_subscription_pricing" "storage" {
#   tier          = "Standard"
#   resource_type = "StorageAccounts"
# }

# resource "azurerm_security_center_subscription_pricing" "containers" {
#   tier          = "Standard"
#   resource_type = "ContainerRegistry"
# }

# Note: PostgreSQL configurations are not applicable for Container Instances
# This project uses PostgreSQL in a container (see database.tf)
# For production, consider migrating to Azure PostgreSQL Flexible Server for:
# - Better security controls
# - Automated backups
# - High availability
# - Advanced monitoring

# Container Registry security settings - already in container-registry.tf
# Ensure admin user is disabled in production

# Variables for security configuration
variable "enable_advanced_threat_protection" {
  description = "Enable Advanced Threat Protection (additional cost)"
  type        = bool
  default     = false
}

variable "allowed_management_ips" {
  description = "List of IP addresses allowed to manage resources"
  type        = list(string)
  default     = []
}

