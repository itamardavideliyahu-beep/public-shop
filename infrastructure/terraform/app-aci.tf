# Main Application Container Instance
# Note: This will be deployed after CI/CD pipeline builds the Docker image
resource "azurerm_container_group" "app" {
  count = var.deploy_app_container ? 1 : 0
  name                = "aci-app-${var.project_name}-${var.environment}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  ip_address_type     = "Public"
  os_type             = "Linux"
  restart_policy      = "Always"
  dns_name_label      = "app-${var.project_name}-${var.environment}"

  container {
    name   = "app"
    image  = "${azurerm_container_registry.main.login_server}/${var.project_name}:latest"
    cpu    = "1.0"
    memory = "2.0"

    ports {
      port     = 8000
      protocol = "TCP"
    }

    # Environment variables
    environment_variables = {
      # Flask Configuration
      FLASK_ENV   = "production"
      FLASK_DEBUG = "False"
      SECRET_KEY  = random_password.flask_secret_key.result

      # Database Configuration (PostgreSQL ACI)
      POSTGRES_USER     = "psqladmin"
      POSTGRES_PASSWORD = random_password.postgres_password.result
      POSTGRES_DB       = "public_shop"
      POSTGRES_HOST     = var.deploy_database_containers ? azurerm_container_group.postgres[0].ip_address : "localhost"
      POSTGRES_PORT     = "5432"
      DATABASE_URL      = var.deploy_database_containers ? "postgresql://psqladmin:${random_password.postgres_password.result}@${azurerm_container_group.postgres[0].ip_address}:5432/public_shop" : "sqlite:///app.db"

      # Redis Configuration (Container Instance)
      REDIS_HOST            = var.deploy_database_containers ? azurerm_container_group.redis[0].ip_address : "localhost"
      REDIS_PORT            = "6379"
      REDIS_PASSWORD        = random_password.redis_password.result
      RATELIMIT_STORAGE_URL = local.redis_url
      CACHE_TYPE            = "RedisCache"
      CACHE_REDIS_URL       = local.redis_url
      CACHE_DEFAULT_TIMEOUT = "300"

      # Security
      # SESSION_COOKIE_SECURE must be False for HTTP (ACI without HTTPS)
      SESSION_COOKIE_SECURE   = "False"
      SESSION_COOKIE_HTTPONLY = "True"
      SESSION_LIFETIME        = "86400"

      # Application Insights
      APPINSIGHTS_INSTRUMENTATIONKEY        = azurerm_application_insights.main.instrumentation_key
      APPLICATIONINSIGHTS_CONNECTION_STRING = azurerm_application_insights.main.connection_string

      # File Uploads
      MAX_UPLOAD_SIZE = "16777216" # 16MB
      MAX_IMAGE_SIZE  = "5242880"  # 5MB

      # Pagination
      POSTS_PER_PAGE         = "20"
      LISTINGS_PER_PAGE      = "20"
      CONVERSATIONS_PER_PAGE = "20"

      # Email Configuration
      MAIL_SERVER         = var.mail_server
      MAIL_PORT           = tostring(var.mail_port)
      MAIL_USE_TLS        = tostring(var.mail_use_tls)
      MAIL_USERNAME       = var.mail_username != "" ? azurerm_key_vault_secret.mail_username.value : ""
      MAIL_PASSWORD       = var.mail_password != "" ? azurerm_key_vault_secret.mail_password.value : ""
      MAIL_DEFAULT_SENDER = var.mail_default_sender
    }
  }

  # Registry credentials for ACR
  image_registry_credential {
    server   = azurerm_container_registry.main.login_server
    username = azurerm_container_registry.main.admin_username
    password = azurerm_container_registry.main.admin_password
  }

  # Ensure dependencies are created before App ACI
  depends_on = [
    azurerm_container_registry.main,
    azurerm_container_group.redis,
    azurerm_container_group.postgres,
    azurerm_key_vault_secret.postgres_password,
    azurerm_key_vault_secret.redis_password,
    azurerm_key_vault_secret.secret_key,
  ]

  tags = var.tags
}

