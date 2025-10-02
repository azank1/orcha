// Test script for accept order invariants
// Ensures proxy rejects invalid price combinations

/// <reference types="node" />

import axios from "axios";

const rpc = (method: string, params: any) =>
  axios.post("http://127.0.0.1:8080/rpc", {
    jsonrpc: "2.0",
    id: Date.now(),
    method,
    params
  });

console.log("=== Testing Accept Order Invariants ===\n");

(async () => {
  // Test 1: canonical < menuPrice should be rejected
  console.log("[1/3] Testing: canonicalPrice < menuPrice (should fail)");
  try {
    await rpc("foodtec.accept_order", {
      category: "Appetizer",
      item: "3pcs Chicken Strips w/ FF",
      size: "Lg",
      customer: { name: "Test User", phone: "410-555-1234" },
      menuPrice: 6.99,
      canonicalPrice: 6.50, // WRONG: less than menu price
      externalRef: "ext-bad-1",
      idem: "bad-1"
    });
    console.error("❌ Expected failure but got success");
    process.exit(1);
  } catch (e: any) {
    const errorMsg = e.response?.data?.error?.message || e.message;
    if (errorMsg.includes("canonicalPrice") && errorMsg.includes("menuPrice")) {
      console.log("✓ Invariant caught:", errorMsg, "\n");
    } else {
      console.error("❌ Wrong error message:", errorMsg);
      process.exit(1);
    }
  }

  // Test 2: Invalid phone format should be rejected
  console.log("[2/3] Testing: Invalid phone format (should fail)");
  try {
    await rpc("foodtec.accept_order", {
      category: "Appetizer",
      item: "3pcs Chicken Strips w/ FF",
      size: "Lg",
      customer: { name: "Test User", phone: "1234567890" }, // WRONG: no dashes
      menuPrice: 6.99,
      canonicalPrice: 7.41,
      externalRef: "ext-bad-2",
      idem: "bad-2"
    });
    console.error("❌ Expected failure but got success");
    process.exit(1);
  } catch (e: any) {
    const errorMsg = e.response?.data?.error?.message || e.message;
    if (errorMsg.includes("phone")) {
      console.log("✓ Phone validation caught:", errorMsg, "\n");
    } else {
      console.error("❌ Wrong error message:", errorMsg);
      process.exit(1);
    }
  }

  // Test 3: Negative prices should be rejected
  console.log("[3/3] Testing: Negative prices (should fail)");
  try {
    await rpc("foodtec.accept_order", {
      category: "Appetizer",
      item: "3pcs Chicken Strips w/ FF",
      size: "Lg",
      customer: { name: "Test User", phone: "410-555-1234" },
      menuPrice: -6.99, // WRONG: negative
      canonicalPrice: 7.41,
      externalRef: "ext-bad-3",
      idem: "bad-3"
    });
    console.error("❌ Expected failure but got success");
    process.exit(1);
  } catch (e: any) {
    const errorMsg = e.response?.data?.error?.message || e.message;
    if (errorMsg.includes("Prices must be")) {
      console.log("✓ Price validation caught:", errorMsg, "\n");
    } else {
      console.error("❌ Wrong error message:", errorMsg);
      process.exit(1);
    }
  }

  console.log("=== All Invariant Tests Passed ✓ ===");
  process.exit(0);
})();
