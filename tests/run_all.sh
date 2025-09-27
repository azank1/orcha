#!/bin/bash
# One-command test runner for Linux/macOS

echo "🧪 Running All Tests"
echo "===================="

# Test 1: P2A Direct API
echo "1️⃣ P2A Direct API Test..."
python tests/test_smoke_p2a.py
if [ $? -ne 0 ]; then
    echo "❌ P2A test failed"
    exit 1
fi

echo ""
echo "2️⃣ Starting Proxy Server..."
cd proxy
python main.py &
PROXY_PID=$!
cd ..

# Wait for server to start
sleep 3

# Test 2: Proxy JSON-RPC
echo "3️⃣ Proxy JSON-RPC Test..."
python tests/test_smoke_proxy.py
PROXY_TEST_RESULT=$?

# Clean up
echo "🧹 Stopping Proxy Server..."
kill $PROXY_PID 2>/dev/null

if [ $PROXY_TEST_RESULT -ne 0 ]; then
    echo "❌ Proxy test failed"
    exit 1
fi

echo ""
echo "🎉 All tests passed!"
echo "✅ P2A Direct API working"
echo "✅ Proxy JSON-RPC working"
echo "✅ End-to-end integration complete"