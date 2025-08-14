#!/usr/bin/env node

/**
 * Performance Test Suite for Open Stream AI Application
 * Tests startup time, model loading, and analysis performance
 */

const axios = require("axios");
const { performance } = require("perf_hooks");
const { spawn } = require("child_process");
const fs = require("fs");
const path = require("path");

class PerformanceTest {
  constructor() {
    this.baseUrl = "http://127.0.0.1";
    this.port = null;
    this.results = {};
    this.testTexts = [
      "This is a great day!",
      "I hate this stupid thing",
      "The weather is nice today",
      "You are an idiot",
      "I love programming",
      "This code is terrible",
      "Amazing work on this project",
      "Kill this process now",
      "Beautiful sunset tonight",
      "This is garbage",
    ];
  }

  async findServerPort() {
    // Look for running server or start new one
    for (let port = 55555; port < 55565; port++) {
      try {
        const response = await axios.get(`http://127.0.0.1:${port}/health`, {
          timeout: 1000,
        });
        if (
          response.data.status === "healthy" ||
          response.data.status === "ok"
        ) {
          this.port = port;
          console.log(`✅ Found running server on port ${port}`);
          return true;
        }
      } catch (error) {
        // Continue checking other ports
      }
    }
    return false;
  }

  async waitForServer(maxAttempts = 60) {
    console.log("⏳ Waiting for server to be ready...");

    for (let i = 0; i < maxAttempts; i++) {
      try {
        const response = await axios.get(
          `${this.baseUrl}:${this.port}/health`,
          { timeout: 2000 }
        );
        if (
          response.data.status === "healthy" ||
          response.data.status === "ok"
        ) {
          console.log("✅ Server is ready!");
          return true;
        }
      } catch (error) {
        // Not ready yet
      }

      await new Promise((resolve) => setTimeout(resolve, 1000));
    }

    return false;
  }

  async testServerStartup() {
    console.log("\n🚀 Testing Server Startup Performance...");
    const startTime = performance.now();

    if (await this.findServerPort()) {
      this.results.serverStartup = {
        existingServer: true,
        time: performance.now() - startTime,
        status: "ready",
      };
      return true;
    }

    // If no server found, test results show this is a cold start scenario
    console.log(
      "❌ No running server found. This test requires a running server."
    );
    this.results.serverStartup = {
      existingServer: false,
      time: performance.now() - startTime,
      status: "not_found",
    };
    return false;
  }

  async testFirstAnalysis() {
    console.log("\n🧠 Testing First Analysis Performance (Model Loading)...");
    const startTime = performance.now();

    try {
      const response = await axios.post(
        `${this.baseUrl}:${this.port}/analyze`,
        {
          text: "Test message for performance analysis",
          include_toxicity: true,
          include_sentiment: true,
          include_emotions: false,
          include_hate_speech: false,
        },
        { timeout: 120000 }
      ); // 2 minute timeout for model loading

      const endTime = performance.now();
      const responseTime = endTime - startTime;

      this.results.firstAnalysis = {
        responseTime,
        processingTime: response.data.processing_time_ms,
        aiEnabled: response.data.ai_enabled,
        models: response.data.model_versions,
        success: true,
      };

      console.log(
        `✅ First analysis completed in ${responseTime.toFixed(2)}ms`
      );
      console.log(
        `   - Server processing: ${response.data.processing_time_ms}ms`
      );
      console.log(`   - AI enabled: ${response.data.ai_enabled}`);

      return response.data;
    } catch (error) {
      this.results.firstAnalysis = {
        responseTime: performance.now() - startTime,
        error: error.message,
        success: false,
      };
      console.log(`❌ First analysis failed: ${error.message}`);
      return null;
    }
  }

  async testSubsequentAnalyses() {
    console.log("\n⚡ Testing Subsequent Analysis Performance (Caching)...");

    const results = [];

    for (let i = 0; i < this.testTexts.length; i++) {
      const text = this.testTexts[i];
      const startTime = performance.now();

      try {
        const response = await axios.post(
          `${this.baseUrl}:${this.port}/analyze`,
          {
            text,
            include_toxicity: true,
            include_sentiment: true,
            include_emotions: false,
            include_hate_speech: false,
          },
          { timeout: 10000 }
        );

        const endTime = performance.now();
        const responseTime = endTime - startTime;

        results.push({
          text: text.substring(0, 30) + (text.length > 30 ? "..." : ""),
          responseTime,
          processingTime: response.data.processing_time_ms,
          toxic: response.data.toxic,
          sentiment: response.data.sentiment,
          cacheHit: response.data.cache_hit || false,
        });

        console.log(
          `${i + 1}/10 - ${responseTime.toFixed(2)}ms - ${text.substring(0, 30)}...`
        );
      } catch (error) {
        results.push({
          text,
          error: error.message,
          responseTime: performance.now() - startTime,
        });
        console.log(`❌ Analysis ${i + 1} failed: ${error.message}`);
      }
    }

    this.results.subsequentAnalyses = {
      tests: results,
      averageResponseTime:
        results.reduce((sum, r) => sum + (r.responseTime || 0), 0) /
        results.length,
      averageProcessingTime:
        results.reduce((sum, r) => sum + (r.processingTime || 0), 0) /
        results.length,
    };

    console.log(
      `📊 Average response time: ${this.results.subsequentAnalyses.averageResponseTime.toFixed(2)}ms`
    );
    console.log(
      `📊 Average processing time: ${this.results.subsequentAnalyses.averageProcessingTime.toFixed(2)}ms`
    );
  }

  async testPerformanceEndpoint() {
    console.log("\n📊 Testing Performance Monitoring Endpoint...");

    try {
      const response = await axios.get(
        `${this.baseUrl}:${this.port}/performance`,
        { timeout: 5000 }
      );

      this.results.performanceStats = response.data;

      console.log("✅ Performance stats retrieved:");
      console.log(
        `   - Memory usage: ${response.data.ai_manager?.memory_usage_mb}MB`
      );
      console.log(
        `   - Models loaded: ${response.data.ai_manager?.models_loaded}`
      );
      console.log(`   - Cache size: ${response.data.ai_manager?.cache_size}`);
      console.log(
        `   - Background loading: ${response.data.ai_manager?.background_loading}`
      );

      if (response.data.system) {
        console.log(`   - CPU usage: ${response.data.system.cpu_percent}%`);
        console.log(
          `   - Memory percent: ${response.data.system.memory_percent}%`
        );
      }
    } catch (error) {
      this.results.performanceStats = {
        error: error.message,
      };
      console.log(`❌ Performance endpoint failed: ${error.message}`);
    }
  }

  async testConcurrentRequests() {
    console.log("\n🔄 Testing Concurrent Request Performance...");

    const concurrentRequests = 5;
    const requests = [];

    const startTime = performance.now();

    for (let i = 0; i < concurrentRequests; i++) {
      const text = this.testTexts[i % this.testTexts.length];

      const requestPromise = axios.post(
        `${this.baseUrl}:${this.port}/analyze`,
        {
          text,
          include_toxicity: true,
          include_sentiment: true,
        },
        { timeout: 10000 }
      );

      requests.push(requestPromise);
    }

    try {
      const results = await Promise.allSettled(requests);
      const endTime = performance.now();

      const successful = results.filter((r) => r.status === "fulfilled").length;
      const failed = results.filter((r) => r.status === "rejected").length;

      this.results.concurrentRequests = {
        totalTime: endTime - startTime,
        successful,
        failed,
        throughput: (successful / ((endTime - startTime) / 1000)).toFixed(2),
      };

      console.log(`✅ Concurrent requests completed:`);
      console.log(`   - Total time: ${(endTime - startTime).toFixed(2)}ms`);
      console.log(`   - Successful: ${successful}/${concurrentRequests}`);
      console.log(
        `   - Throughput: ${this.results.concurrentRequests.throughput} req/sec`
      );
    } catch (error) {
      this.results.concurrentRequests = {
        error: error.message,
      };
      console.log(`❌ Concurrent request test failed: ${error.message}`);
    }
  }

  generateReport() {
    console.log("\n📈 Performance Test Report");
    console.log("=".repeat(50));

    const report = {
      timestamp: new Date().toISOString(),
      results: this.results,
      summary: this.generateSummary(),
    };

    // Save report to file
    const reportPath = path.join(__dirname, "performance-report.json");
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

    console.log("\n📊 Summary:");
    Object.entries(report.summary).forEach(([key, value]) => {
      console.log(`   ${key}: ${value}`);
    });

    console.log(`\n💾 Full report saved to: ${reportPath}`);

    return report;
  }

  generateSummary() {
    const summary = {};

    if (this.results.firstAnalysis?.success) {
      summary["First Response Time"] =
        `${this.results.firstAnalysis.responseTime.toFixed(2)}ms`;
    }

    if (this.results.subsequentAnalyses) {
      summary["Avg Subsequent Response"] =
        `${this.results.subsequentAnalyses.averageResponseTime.toFixed(2)}ms`;
    }

    if (this.results.performanceStats?.ai_manager) {
      summary["Memory Usage"] =
        `${this.results.performanceStats.ai_manager.memory_usage_mb}MB`;
      summary["Models Loaded"] =
        this.results.performanceStats.ai_manager.models_loaded;
      summary["Cache Size"] =
        this.results.performanceStats.ai_manager.cache_size;
    }

    if (this.results.concurrentRequests?.throughput) {
      summary["Throughput"] =
        `${this.results.concurrentRequests.throughput} req/sec`;
    }

    return summary;
  }
}

async function runPerformanceTest() {
  console.log("🧪 Open Stream AI Performance Test Suite");
  console.log("=".repeat(50));

  const tester = new PerformanceTest();

  try {
    // Test 1: Server Startup
    const serverReady = await tester.testServerStartup();
    if (!serverReady) {
      console.log("\n❌ Cannot continue without a running server.");
      console.log("💡 Please start the server first with: pnpm dev");
      return;
    }

    // Test 2: First Analysis (Model Loading)
    await tester.testFirstAnalysis();

    // Test 3: Subsequent Analyses (Caching Performance)
    await tester.testSubsequentAnalyses();

    // Test 4: Performance Monitoring
    await tester.testPerformanceEndpoint();

    // Test 5: Concurrent Requests
    await tester.testConcurrentRequests();

    // Generate Report
    const report = tester.generateReport();

    // Performance Targets Check
    console.log("\n🎯 Performance Targets:");
    const firstResponse =
      tester.results.firstAnalysis?.responseTime || Infinity;
    const avgSubsequent =
      tester.results.subsequentAnalyses?.averageResponseTime || Infinity;

    console.log(
      `   First Response: ${firstResponse < 5000 ? "✅" : "❌"} ${firstResponse.toFixed(2)}ms (target: <5000ms)`
    );
    console.log(
      `   Avg Subsequent: ${avgSubsequent < 500 ? "✅" : "❌"} ${avgSubsequent.toFixed(2)}ms (target: <500ms)`
    );

    const memoryMB =
      tester.results.performanceStats?.ai_manager?.memory_usage_mb || 0;
    console.log(
      `   Memory Usage: ${memoryMB < 1000 ? "✅" : "❌"} ${memoryMB}MB (target: <1000MB)`
    );
  } catch (error) {
    console.error("❌ Performance test failed:", error);
  }
}

if (require.main === module) {
  runPerformanceTest();
}

module.exports = { PerformanceTest };
