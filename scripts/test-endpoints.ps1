# Test All Orcha-2 Endpoints
# Usage: .\scripts\test-endpoints.ps1

Write-Host "🧪 Testing Orcha-2 Endpoints..." -ForegroundColor Green

$baseUrl = "http://127.0.0.1:8000"

Write-Host "`n1. Testing Basic Health..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$baseUrl/health" -Method GET
    Write-Host "✅ Health: $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "❌ Health check failed" -ForegroundColor Red
    exit 1
}

Write-Host "`n2. Testing LLM Health..." -ForegroundColor Yellow  
try {
    $llmHealth = Invoke-RestMethod -Uri "$baseUrl/automation/health/llm" -Method GET
    Write-Host "✅ Ollama: $($llmHealth.ollama), OpenAI: $($llmHealth.openai)" -ForegroundColor Green
} catch {
    Write-Host "❌ LLM health check failed" -ForegroundColor Red
}

Write-Host "`n3. Testing Search..." -ForegroundColor Yellow
try {
    $search = Invoke-RestMethod -Uri "$baseUrl/automation/search?query=pizza" -Method GET
    Write-Host "✅ Search returned $($search.results.Count) results" -ForegroundColor Green
} catch {
    Write-Host "❌ Search test failed" -ForegroundColor Red
}

Write-Host "`n4. Testing Session-Aware Orchestration..." -ForegroundColor Yellow
try {
    $orchestrate = Invoke-RestMethod -Uri "$baseUrl/automation/orchestrate" -Method POST -ContentType "application/json" -Body '{"text": "find pizza"}'
    Write-Host "✅ Orchestration: $($orchestrate.event), LLM: $($orchestrate.llm_source)" -ForegroundColor Green
    $sessionId = $orchestrate.data.session_id
    Write-Host "   Session ID: $sessionId" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Orchestration test failed" -ForegroundColor Red
}

Write-Host "`n5. Testing Session Stats..." -ForegroundColor Yellow
try {
    $stats = Invoke-RestMethod -Uri "$baseUrl/automation/sessions/stats" -Method GET
    Write-Host "✅ Active sessions: $($stats.active_sessions)" -ForegroundColor Green
} catch {
    Write-Host "❌ Session stats failed" -ForegroundColor Red
}

Write-Host "`n🎉 Endpoint testing complete!" -ForegroundColor Green