variable "environment" {
  description = "Environment name (dev, staging, prod, poc)"
  type        = string
  default     = "poc"
}

variable "deploy_app_container" {
  description = "Whether to deploy the app container (set to false until Docker image is built by CI/CD)"
  type        = bool
  default     = false
}

variable "deploy_database_containers" {
  description = "Whether to deploy database and redis containers (set to false if having issues with Docker Hub)"
  type        = bool
  default     = false
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "eastus"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "public-shop"
}

variable "app_service_sku" {
  description = "App Service Plan SKU - DEPRECATED: Using ACI instead, this variable is kept for backward compatibility"
  type        = string
  default     = "F1" # Not used anymore - ACI doesn't use App Service Plan
}

variable "postgres_sku_name" {
  description = "PostgreSQL SKU name"
  type        = string
  default     = "B_Standard_B1ms" # Burstable tier, can be upgraded to GeneralPurpose or MemoryOptimized
}

variable "postgres_storage_mb" {
  description = "PostgreSQL storage in MB"
  type        = number
  default     = 32768 # 32 GB
}

variable "postgres_version" {
  description = "PostgreSQL version"
  type        = string
  default     = "15"
}

variable "redis_host" {
  description = "Redis host (Docker container name or hostname)"
  type        = string
  default     = "redis"
}

variable "redis_port" {
  description = "Redis port"
  type        = number
  default     = 6379
}

variable "redis_password" {
  description = "Redis password (leave empty for no password)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "redis_use_ssl" {
  description = "Use SSL/TLS for Redis connection"
  type        = bool
  default     = false
}

variable "container_registry_sku" {
  description = "Container Registry SKU (Basic, Standard, Premium)"
  type        = string
  default     = "Basic"
}

variable "storage_account_tier" {
  description = "Storage account tier (Standard, Premium)"
  type        = string
  default     = "Standard"
}

variable "storage_account_replication_type" {
  description = "Storage account replication type"
  type        = string
  default     = "LRS" # Locally Redundant Storage
}

variable "allowed_ip_addresses" {
  description = "List of allowed IP addresses for database access"
  type        = list(string)
  default     = []
}

variable "enable_private_endpoint" {
  description = "Enable private endpoints for resources"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Environment = "poc"
    Project     = "public-shop"
    ManagedBy   = "Terraform"
    Owner       = "DevOps"
    CostCenter  = "Engineering"
    Compliance  = "Standard"
  }
  
  validation {
    condition     = contains(keys(var.tags), "Environment")
    error_message = "Tags must include an 'Environment' key."
  }
}

# Service Principal Authentication Variables
variable "subscription_id" {
  description = "Azure subscription ID"
  type        = string
  sensitive   = false
}

variable "client_id" {
  description = "Azure service principal client ID (application ID)"
  type        = string
  sensitive   = false
}

variable "client_secret" {
  description = "Azure service principal client secret"
  type        = string
  sensitive   = true
}

variable "tenant_id" {
  description = "Azure tenant ID"
  type        = string
  sensitive   = false
}

# Email Configuration Variables
variable "mail_username" {
  description = "Email username for sending notifications (e.g., your-email@gmail.com)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "mail_password" {
  description = "Email password or app-specific password (use Gmail App Password, not regular password!)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "mail_server" {
  description = "SMTP server for email"
  type        = string
  default     = "smtp.gmail.com"
}

variable "mail_port" {
  description = "SMTP port for email"
  type        = number
  default     = 587
}

variable "mail_use_tls" {
  description = "Use TLS for email connections"
  type        = bool
  default     = true
}

variable "mail_default_sender" {
  description = "Default sender email address"
  type        = string
  default     = "noreply@publicshop.com"
}

