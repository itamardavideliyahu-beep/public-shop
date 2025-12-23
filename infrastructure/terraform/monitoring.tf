# Application Insights Alerts and Monitoring Configuration

# Alert for high error rate
resource "azurerm_monitor_metric_alert" "high_error_rate" {
  name                = "${local.resource_prefix}-high-error-rate"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_application_insights.main.id]
  description         = "Alert when error rate is too high"
  severity            = 2
  frequency           = "PT5M"
  window_size         = "PT15M"

  criteria {
    metric_namespace = "microsoft.insights/components"
    metric_name      = "exceptions/count"
    aggregation      = "Count"
    operator         = "GreaterThan"
    threshold        = 10
  }

  action {
    action_group_id = azurerm_monitor_action_group.main.id
  }

  tags = local.common_tags
}

# Alert for slow response time
resource "azurerm_monitor_metric_alert" "slow_response_time" {
  name                = "${local.resource_prefix}-slow-response"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_application_insights.main.id]
  description         = "Alert when response time is too slow"
  severity            = 3
  frequency           = "PT5M"
  window_size         = "PT15M"

  criteria {
    metric_namespace = "microsoft.insights/components"
    metric_name      = "requests/duration"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 5000  # 5 seconds
  }

  action {
    action_group_id = azurerm_monitor_action_group.main.id
  }

  tags = local.common_tags
}

# Note: Database alerts for PostgreSQL Flexible Server are not applicable
# This project uses Container Instances with PostgreSQL in a container
# For production, consider migrating to Azure PostgreSQL Flexible Server for better monitoring

# Action Group for alerts
resource "azurerm_monitor_action_group" "main" {
  name                = "${local.resource_prefix}-action-group"
  resource_group_name = azurerm_resource_group.main.name
  short_name          = "shopAlert"

  # Email notification (add your email)
  email_receiver {
    name                    = "DevOps Team"
    email_address           = var.alert_email_address
    use_common_alert_schema = true
  }

  # Optional: Webhook notification
  # webhook_receiver {
  #   name        = "slack-webhook"
  #   service_uri = var.slack_webhook_url
  # }

  tags = local.common_tags
}

# Variables for monitoring
variable "alert_email_address" {
  description = "Email address for alert notifications"
  type        = string
  default     = "devops@example.com"
}

# Optional: Diagnostic settings for container instances
# Note: Container Instances don't support all diagnostic settings,
# but we can enable logging to Log Analytics Workspace

# Log Analytics Workspace is already defined in app-insights.tf
# We reuse the existing workspace for all monitoring and diagnostic settings

# Link Application Insights to Log Analytics
resource "azurerm_monitor_diagnostic_setting" "app_insights" {
  name                       = "${local.resource_prefix}-appinsights-diag"
  target_resource_id         = azurerm_application_insights.main.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id

  enabled_log {
    category = "AppTraces"
  }

  enabled_log {
    category = "AppRequests"
  }

  enabled_log {
    category = "AppExceptions"
  }

  metric {
    category = "AllMetrics"
  }
}

# Note: Database diagnostic settings are not applicable for Container Instances
# PostgreSQL is running in a container, not as a managed service

