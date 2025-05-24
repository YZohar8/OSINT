
# answers.md

## 1. Additional Production-Grade Tests

- **Concurrency Stress Handling**:  
  During development, I noticed that running multiple scans in parallel can cause significant CPU and memory load, sometimes leading to system instability. As a mitigation, I changed the logic to queue scans and execute them one after the other.  
  In production, I would implement robust concurrency stress tests to validate system behavior under heavy load, simulating multiple simultaneous user requests.

- **Load Testing**:  
  I would add load tests to measure how the system handles various numbers of concurrent domain scans. Tools like `Locust` or `k6` can simulate traffic and help identify breaking points or latency issues.

## 2. Benchmarking & Performance Optimization

- **Execution Time Monitoring**:  
  I would integrate performance logging to track the time taken by each component (e.g., domain submission, OSINT tool execution, result aggregation). This allows identifying specific slow points.

- **Task Splitting**:  
  Rather than executing large, heavy scans, I would split tasks into multiple smaller operations that can be processed in parallel. This not only improves responsiveness but also allows partial results to be displayed earlier.

- **Selective Tool Execution**:  
  For tools or data sources that are slow and contribute limited value, I would consider disabling them or making them optional to improve overall performance.

## 3. Known Bottlenecks in OSINT Tools & Mitigations

| Tool         | Bottleneck                                        | Mitigation Strategy                                                   |
|--------------|---------------------------------------------------|------------------------------------------------------------------------|
| theHarvester | Long scan durations depending on enabled sources | Allow selective source configuration and run in a subprocess          |
| Amass        | High memory usage, especially in active mode     | Run in passive mode only; limit recursion and use safe subprocess API |
| Both         | Parallel execution can overload system resources | Execute one scan at a time, or use task queueing with concurrency limits |

Additionally, splitting scans into smaller chunks and executing those in parallel often yields faster and more manageable results than running one large scan per tool.

## 4. Bonus – Additional Passive OSINT Tool

*Not implemented in this version.*

