$startTime = Get-Date
$env:AZURE_CORE_ONLY_SHOW_ERRORS = "True"

# Generate a random string with 5 characters
$randomString = -join (1..5 | ForEach-Object { [char] (Get-Random -InputObject (48..57 + 97..122)) })

# DECLARE VARIABLES
$tenantId = "" # Enter your Tenant ID
$spn_name = "fastapispn" + $randomString
$rg_name = "fastapirg" + $randomString
$location = "westus"
$storage_account = "fastapibakstorage"  + $randomString
$storage_container = "backups"
$azuresqldbserver = "fastapisqlserver" + $randomString
$sqluseradmin = "fastapisqladmin"
$sqluseradminpassword = "S!mpl3#Str0ngP@ss2025"
$bacpacfilename = "AdventureWorks2019.bacpac"
$azuresqldbname = "AdventureWorks2019"
$vaultname  = "demosecrets" + $randomString
$startIp = "0.0.0.0"
$endIp = "0.0.0.0"
$myIpStart = "" #Enter your IP value
$myIpEnd = "" #Enter your IP value
Write-Host "Variables declared successfully." -ForegroundColor Green

# Ensure Tenant ID is provided
if (-not $tenantId) {
    Write-Host "Error: Tenant ID is missing. Please provide a valid tenant ID." -ForegroundColor Red
    exit
}

# Connect to Azure subscription
try {
    az login --tenant $tenantId
    Write-Host "Login successful." -ForegroundColor Green
} catch {
    Write-Host "Error logging into Azure: $_" -ForegroundColor Red
    exit
}

# Confirm access to the tenant
try {
    az account list
    Write-Host "Azure account listed successfully." -ForegroundColor Green
} catch {
    Write-Host "Error retrieving Azure account list: $_" -ForegroundColor Red
}

# Get Subscription ID and User Principal ID, for later use
$subscriptionId = az account show --query id --output tsv
$userPrincipalId = az ad signed-in-user show --query id --output tsv

# Create a Service Principal & store credentials
try {
    $spData = az ad sp create-for-rbac --name $spn_name --query "{appId:appId, password:password}" --output json | ConvertFrom-Json
    $appId = $spData.appId
    $secretPassword = $spData.password

    Write-Host "Service principal created successfully." -ForegroundColor Green
} catch {
    Write-Host "Error creating service principal: $_" -ForegroundColor Red
    exit
}

# Create a Resource Group
try {
    az group create --name $rg_name --location $location
    Write-Host "Resource group created successfully." -ForegroundColor Green
} catch {
    Write-Host "Error creating resource group: $_" -ForegroundColor Red
    exit
}

# Create a Storage Account
try {
    az storage account create --name $storage_account --resource-group $rg_name --location $location --sku Standard_LRS
    Write-Host "Storage account created successfully." -ForegroundColor Green
} catch {
    Write-Host "Error creating storage account: $_" -ForegroundColor Red
    exit
}

# Check if storage account exists before proceeding
$storageExists = az storage account list --resource-group $rg_name --query "[?name=='$storage_account']" --output tsv

if (-not $storageExists) {
    Write-Host "Error: Storage account does not exist." -ForegroundColor Red
    exit
}

# Create a Storage Container
try {
    az storage container create --account-name $storage_account --name $storage_container
    Write-Host "Container created successfully." -ForegroundColor Green
} catch {
    Write-Host "Error creating storage container: $_" -ForegroundColor Red
    exit
}

# Retrieve Storage Credentials
try {
    $storageKey=$(az storage account keys list --account-name $storage_account --resource-group $rg_name --query '[0].value' --output tsv)
    $storageConnectionString="$(az storage account show-connection-string --name $storage_account --resource-group $rg_name --query connectionString --output tsv)"
} catch {
    Write-Host "Error retrieving storage credentials: $_" -ForegroundColor Red
    exit
}

# Upload a File to Storage
try {
    az storage blob upload --account-name $storage_account --container-name $storage_container --file .\_PowerShell_Resources\AdventureWorks2019.bacpac --auth-mode key
    Write-Host "bacpac file uploaded successfully." -ForegroundColor Green
} catch {
    Write-Host "Error uploading bacpac file: $_" -ForegroundColor Red
}

# Validate Upload
try {
    $fileExists = az storage blob list --account-name $storage_account --container-name $storage_container --query "[?name=='AdventureWorks2019.bacpac']" --output tsv

    if ($fileExists) {
        Write-Host "Upload Complete! AdventureWorks2019.bacpac has been successfully uploaded to $storage_container." -ForegroundColor Green
    } else {
        Write-Host "Upload Failed! The file was not found in the storage container." -ForegroundColor Red
    }
} catch {
    Write-Host "Error validating uploaded file: $_" -ForegroundColor Red
}

# Create Azure SQL Server (Logical Server)
try {
    Write-Host "Creating $azuresqldbserver in $location" -ForegroundColor Yellow
    az sql server create --name $azuresqldbserver --resource-group $rg_name --location $location --admin-user $sqluseradmin --admin-password $sqluseradminpassword 
    $dbHostName = $(az sql server list --resource-group $rg_name --query "[].fullyQualifiedDomainName" --output tsv)
    Write-Host "Azure SQL Server (logical server) has been successfully created" -ForegroundColor Green
} catch {
    Write-Host "Error creating the Azure SQL Server (logical server) : $_" -ForegroundColor Red
}

# Configure Firewall Rules
try {
    az sql server firewall-rule create --resource-group $rg_name --server $azuresqldbserver --name "AllowAzureServices" --start-ip-address $startIp --end-ip-address $endIp
    Write-Host "Allow Azure services completed successfully." -ForegroundColor Green
    
    az sql server firewall-rule create --resource-group $rg_name --server $azuresqldbserver --name "MyIP" --start-ip-address $myIpStart --end-ip-address $myIpEnd 
    Write-Host "Allow your current IP completed successfully." -ForegroundColor Green
} catch {
    Write-Host "Error configuring the firewall rules : $_" -ForegroundColor Red
}


# Create the database
try {
    Write-Host "Creating $azuresqldbname database" -ForegroundColor Yellow
    az sql db create --resource-group $rg_name --server $azuresqldbserver --name $azuresqldbname --service-objective "Basic"
    Write-Host "Azure SQL Database has been successfully created" -ForegroundColor Green
} catch {
    Write-Host "Error creating the Azure SQL Database : $_" -ForegroundColor Red
}

# Get the Blob URL for the Bacpac file
try {
    $bacpacurl = az storage blob URL --connection-string $storageConnectionString --container-name $storage_container --name $bacpacfilename
    if ($bacpacurl) {
        Write-Host "URL assigned completed!" -ForegroundColor Green
    } else {
        Write-Host "URL assigned failed." -ForegroundColor Red
    }
} catch {
    Write-Host "Error retrieving the the bacpac file URL : $_" -ForegroundColor Red
}


# Import Database from bacpac
try {
   Write-Host "Importing bacpac file" -ForegroundColor Yellow
   az sql db import --server $azuresqldbserver --name $azuresqldbname --resource-group $rg_name --admin-user $sqluseradmin --admin-password $sqluseradminpassword --storage-key-type "StorageAccessKey" --storage-key $storageKey --storage-uri $bacpacurl  
   Write-Host "Import Database from bacpac completed successfully" -ForegroundColor Green
} catch {
   Write-Host "Import Database from bacpac failed : $_" -ForegroundColor Red
}

# Verify the Database creation
az sql db show --resource-group $rg_name --server $azuresqldbserver --name $azuresqldbname

# Create Azure KeyVault
try {
    Write-Host "Creating Azure Key Vault" -ForegroundColor Yellow
    $vault_uri = az keyvault create --name $vaultname --resource-group $rg_name --location $location --query properties.vaultUri --output tsv
    $keyvaultId = $(az keyvault show --name $vaultname --query id --output tsv)

    # Grant full access to the current user
    az role assignment create --assignee $userPrincipalId --role "Key Vault Administrator" --scope /subscriptions/$subscriptionId/resourceGroups/$rg_name/providers/Microsoft.KeyVault/vaults/$vaultname 

    Write-Host "Azure Key Vault creation completed successfully" -ForegroundColor Green
} catch {
    Write-Host "Azure Key Vault creation failed : $_" -ForegroundColor Red
}

# Assign the "Key Vault Secrets Reader" role to the Service Principal
try {
    Write-Output "Assign Key Vault read access to the service principal" -ForegroundColor Yellow
    az role assignment create --assignee $appId --role "Key Vault Secrets User" --scope $keyvaultId
    Write-Output "Service Principal Role assignment completed successfully!" -ForegroundColor Green
} catch {
    Write-Host "Service Principal Role assignment failed : $_" -ForegroundColor Red
}

# Add secrets to the Azure Key Vault
try {
    Write-Host "Adding App ID, App Secret, UserDB Name, UserDB password, and storage connection string to the vault" -ForegroundColor Yellow
    
    $errorOccurred = $false  # Initialize error flag
    
    # Corrected commands array
    $commands = @(
        "az keyvault secret set --vault-name $vaultname --name 'demoapplicationid' --value $appId",
        "az keyvault secret set --vault-name $vaultname --name 'demoapplicationsecret' --value $secretPassword",
        "az keyvault secret set --vault-name $vaultname --name 'sqlusername' --value $sqluseradmin",
        "az keyvault secret set --vault-name $vaultname --name 'sqlpassword' --value $sqluseradminpassword" #,
        # "az keyvault secret set --vault-name $vaultname --name 'storageprimarykey' --value $storageKey",
        # "az keyvault secret set --vault-name $vaultname --name 'storageconnectionstring' --value $storageConnectionString"
    )

    foreach ($cmd in $commands) {
        Invoke-Expression $cmd
        if (-not $?) { $errorOccurred = $true }
    }

    if (-not $errorOccurred) {
        Write-Host "Secrets added successfully" -ForegroundColor Green
    } else {
        throw "Some secrets failed to be added."
    }
} catch {
    Write-Host "Azure Key Vault secret addition failed: $_" -ForegroundColor Red
}

# Display config values to be used in the .env file of the FastAPI code:
    Write-Output "-----------------------------------------------------------------------------" 
    Write-Output "VALUES FOR THE .env FILE" 
    Write-Output "-----------------------------------------------------------------------------" 
    Write-Output "AZURE_SUBSCRIPTION_ID: $subscriptionId"
    Write-Output "AZURE_CLIENT_ID: $appId"
    Write-Output "AZURE_CLIENT_SECRET: $secretPassword"
    Write-Output "AZURE_TENANT_ID: $tenantId"
    Write-Output "KEY_VAULT_URL : $vault_uri"
    Write-Output "DB_HOST : $dbHostName"
    Write-Output "DB_NAME : $azuresqldbname"
    # Write-Output "-----------------------------------------------------------------------------" 
    # Write-Output "Additional values, just in case" 
    # Write-Output "-----------------------------------------------------------------------------" 
    # Write-Output "The storage key is : $storageKey"
    # Write-Output "The Storage Connection string is: $storageConnectionString"
    # Write-Output "-----------------------------------------------------------------------------" 
    # Write-Output "-----------------------------------------------------------------------------" 

$endTime = Get-Date
$duration = $endTime - $startTime
$formattedDuration = "{0:D2} hrs {1:D2} mins {2:D2} secs" -f $duration.Hours, $duration.Minutes, $duration.Seconds
Write-Host "Script execution time: $formattedDuration" -ForegroundColor Green

# Delete the Azure Resource Group, use the below command or the Azure Portal
# az group delete --resource-group replace_with_your_resource_group_name --yes --no-wait