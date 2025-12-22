# Deployment script for Public Shop (PowerShell version)
# This script automates deployment tasks EXCEPT Terraform commands
# Terraform commands (init, plan, apply) should be run manually

$ErrorActionPreference = "Stop"

# Colors
function Write-Info { 
    Write-Host "[INFO] $args" -ForegroundColor Green 
}

function Write-Warn { 
    Write-Host "[WARN] $args" -ForegroundColor Yellow 
}

function Write-Error { 
    Write-Host "[ERROR] $args" -ForegroundColor Red 
}

function Write-Note { 
    Write-Host "[NOTE] $args" -ForegroundColor Cyan 
}

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$TerraformDir = Join-Path (Split-Path -Parent $ScriptDir) "terraform"

# Check if terraform.tfvars exists
if (-not (Test-Path (Join-Path $TerraformDir "terraform.tfvars"))) {
    Write-Error "terraform.tfvars not found in $TerraformDir"
    Write-Error "Please ensure Terraform has been initialized and applied manually first"
    exit 1
}

# Check prerequisites
Write-Info "Checking prerequisites..."

$tools = @("terraform", "az", "docker")
$missingTools = @()

foreach ($tool in $tools) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        $missingTools += $tool
    }
}

if ($missingTools.Count -gt 0) {
    Write-Error "The following tools are not installed: $($missingTools -join ', ')"
    exit 1
}

# Check Azure login
try {
    $null = az account show 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Not logged in"
    }
} catch {
    Write-Warn "Not logged in to Azure. Please run: az login"
    exit 1
}

Write-Info "Prerequisites check passed"
Write-Host ""

# Check if Terraform has been applied
Write-Note "⚠️  IMPORTANT: This script does NOT run Terraform commands"
Write-Note "   Please ensure you have run the following manually:"
Write-Note "   1. cd $TerraformDir"
Write-Note "   2. terraform init"
Write-Note "   3. terraform plan"
Write-Note "   4. terraform apply"
Write-Host ""

# Verify Terraform state exists
$tfStatePath = Join-Path $TerraformDir "terraform.tfstate"
if (-not (Test-Path $tfStatePath)) {
    Write-Error "Terraform state not found. Please run 'terraform apply' first"
    exit 1
}

# Get outputs from Terraform
Write-Info "Reading Terraform outputs..."
Push-Location $TerraformDir

try {
    $ACR_NAME = terraform output -raw container_registry_name 2>$null
    if ($LASTEXITCODE -ne 0) { throw "Failed to get ACR name" }
    
    $APP_CONTAINER_NAME = terraform output -raw app_container_name 2>$null
    if ($LASTEXITCODE -ne 0) { throw "Failed to get App Container name" }
    
    $RESOURCE_GROUP = terraform output -raw resource_group_name 2>$null
    if ($LASTEXITCODE -ne 0) { throw "Failed to get Resource Group name" }
    
    if ([string]::IsNullOrWhiteSpace($ACR_NAME) -or 
        [string]::IsNullOrWhiteSpace($APP_CONTAINER_NAME) -or 
        [string]::IsNullOrWhiteSpace($RESOURCE_GROUP)) {
        throw "One or more outputs are empty"
    }
} catch {
    Write-Error "Could not read Terraform outputs. Please ensure Terraform has been applied"
    Write-Error "Error: $_"
    Pop-Location
    exit 1
}

Write-Info "ACR Name: $ACR_NAME"
Write-Info "App Container Name: $APP_CONTAINER_NAME"
Write-Info "Resource Group: $RESOURCE_GROUP"
Write-Host ""

# Step 1: Pull and push base images (Redis, PostgreSQL) to ACR
$pullImages = Read-Host "Do you want to pull and push base images (Redis, PostgreSQL) to ACR? (yes/no)"
if ($pullImages -eq "yes") {
    Write-Info "Pulling and pushing base images to ACR..."
    
    $ACR_LOGIN_SERVER = "${ACR_NAME}.azurecr.io"
    
    # Login to ACR
    Write-Info "Logging into ACR..."
    az acr login --name $ACR_NAME
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to login to ACR"
        Pop-Location
        exit 1
    }
    
    # Pull Redis
    Write-Info "Pulling Redis image..."
    docker pull redis:7-alpine
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to pull Redis image"
        Pop-Location
        exit 1
    }
    
    # Pull PostgreSQL
    Write-Info "Pulling PostgreSQL image..."
    docker pull postgres:15-alpine
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to pull PostgreSQL image"
        Pop-Location
        exit 1
    }
    
    # Tag Redis
    Write-Info "Tagging Redis image..."
    docker tag redis:7-alpine "${ACR_LOGIN_SERVER}/redis:7"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to tag Redis image"
        Pop-Location
        exit 1
    }
    
    # Tag PostgreSQL
    Write-Info "Tagging PostgreSQL image..."
    docker tag postgres:15-alpine "${ACR_LOGIN_SERVER}/postgres:15-alpine"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to tag PostgreSQL image"
        Pop-Location
        exit 1
    }
    
    # Push Redis
    Write-Info "Pushing Redis image to ACR..."
    docker push "${ACR_LOGIN_SERVER}/redis:7"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to push Redis image"
        Pop-Location
        exit 1
    }
    
    # Push PostgreSQL
    Write-Info "Pushing PostgreSQL image to ACR..."
    docker push "${ACR_LOGIN_SERVER}/postgres:15-alpine"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to push PostgreSQL image"
        Pop-Location
        exit 1
    }
    
    Write-Info "Base images pushed successfully"
    Write-Host ""
}

# Step 2: Build and push application Docker image
$buildImage = Read-Host "Do you want to build and push application Docker image? (yes/no)"
if ($buildImage -eq "yes") {
    Write-Info "Building and pushing application Docker image..."
    
    $ACR_LOGIN_SERVER = "${ACR_NAME}.azurecr.io"
    
    # Login to ACR
    Write-Info "Logging into ACR..."
    az acr login --name $ACR_NAME
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to login to ACR"
        Pop-Location
        exit 1
    }
    
    # Navigate to project root
    $ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)
    Push-Location $ProjectRoot
    
    # Build
    Write-Info "Building Docker image..."
    docker build -t "${ACR_LOGIN_SERVER}/public-shop:latest" .
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to build Docker image"
        Pop-Location
        Pop-Location
        exit 1
    }
    
    # Push
    Write-Info "Pushing Docker image to ACR..."
    docker push "${ACR_LOGIN_SERVER}/public-shop:latest"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to push Docker image"
        Pop-Location
        Pop-Location
        exit 1
    }
    
    Write-Info "Application Docker image pushed successfully"
    Write-Host ""
    
    Pop-Location
}

# Step 3: Run database migrations
$runMigrations = Read-Host "Do you want to run database migrations? (yes/no)"
if ($runMigrations -eq "yes") {
    Write-Info "Running database migrations..."
    Write-Info "App Container: $APP_CONTAINER_NAME"
    Write-Info "Resource Group: $RESOURCE_GROUP"
    Write-Host ""
    Write-Warn "For ACI, you need to run migrations manually:"
    Write-Info "1. Get the container IP:"
    Write-Info "   terraform output app_container_ip"
    Write-Info ""
    Write-Info "2. Execute migration command in the container:"
    Write-Info "   az container exec --resource-group $RESOURCE_GROUP --name $APP_CONTAINER_NAME --exec-command 'flask db upgrade'"
    Write-Host ""
    Write-Info "Or use Azure Portal to connect to the container and run: flask db upgrade"
    Write-Host ""
}

# Display outputs
Write-Host ""
Write-Info "Deployment tasks completed!"
Write-Host ""
Write-Info "Terraform outputs:"
terraform output

Write-Info "Deployment script completed"
Pop-Location

