# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ZLinq is a zero-allocation LINQ library for .NET that provides high-performance alternatives to System.Linq through struct-based value types. The library offers LINQ to Span, LINQ to SIMD, and LINQ to Tree functionality across all .NET platforms including Unity and Godot.

## Key Architecture

### Core Design
- **ValueEnumerable<TEnumerator, T>**: Main struct that wraps enumerators to enable method chaining without allocations
- **IValueEnumerator<T>**: Interface defining `TryGetNext(out T current)` pattern instead of MoveNext/Current
- **ref struct support**: In .NET 9+, ValueEnumerable is a ref struct enabling Span<T> integration
- **Optimization methods**: `TryGetNonEnumeratedCount`, `TryGetSpan`, `TryCopyTo` for performance optimizations

### Project Structure
- `src/ZLinq/`: Core library with all LINQ operators in `Linq/` folder and SIMD implementations in `Simd/`
- `src/ZLinq.DropInGenerator/`: Source generator for automatic ZLinq method replacement
- `src/ZLinq.FileSystem/`, `ZLinq.Json/`, `ZLinq.Godot/`: Tree traversal extensions
- `src/ZLinq.Unity/`: Unity package with GameObject/Transform traversal
- `src/FileGen/`: Code generation tools for creating operators
- `sandbox/`: Test applications and benchmarks
- `tests/`: Comprehensive test suite including System.Linq compatibility tests

## Development Commands

### Building
```bash
dotnet build
```

### Testing
```bash
# Run ZLinq-specific tests
dotnet test tests/ZLinq.Tests/

# Run System.Linq compatibility tests (extensive)
dotnet test tests/System.Linq.Tests/

# Run all tests
dotnet test
```

### Benchmarking
```bash
cd sandbox/Benchmark
dotnet run -c Release
```

## Testing Guidelines

- Use xUnit v3 with Shouldly for assertions
- Global usings include `Xunit`, `Shouldly`, `ZLinq`
- Class field naming: do NOT use `_` prefix
- Tests target multiple frameworks: net6.0, net8.0, net9.0, net48 (Windows), net10.0 (VS Preview)
- System.Linq.Tests project validates 99% compatibility with System.Linq using original Microsoft tests

## Code Patterns

### Custom Operators
- Implement `IValueEnumerator<T>` as struct (ref struct in .NET 9+)
- Use `TryGetNext(out T current)` instead of MoveNext/Current pattern
- Always dispose source enumerators in Dispose()
- Optimization methods can return false if complex to implement

### SIMD Support
- Available in .NET 8+ when `TryGetSpan` returns true
- Covers Sum, Average, Min, Max, Contains, SequenceEqual for numeric types
- Use `ZLinq.Simd` namespace for explicit SIMD operations

### Drop-in Replacement
- Use `ZLinqDropInAttribute` assembly attribute to auto-replace LINQ methods
- Configure with `DropInGenerateTypes` flags for target types
- Support custom types with `ZLinqDropInExtensionAttribute`

## Important Constraints

- ValueEnumerable cannot be converted to IEnumerable<T> in .NET 9+ (ref struct limitation)
- No yield return support in custom operators - everything must be manually implemented
- Reference types in enumerator constructors share state across copies - initialize in TryGetNext instead
- Method chains create different types - cannot reassign to same variable

## Unity Integration

- Install via NuGetForUnity + git URL for Unity package
- Provides GameObject/Transform tree traversal with Ancestors/Children/Descendants
- Supports NativeArray, NativeSlice through AsValueEnumerable()
- Minimum Unity version: 2022.3.12f1 for DropInGenerator support

## Performance Focus

ZLinq prioritizes zero-allocation performance with comprehensive SIMD support and optimization hooks. The library proves compatibility by passing 9000+ System.Linq tests while delivering superior performance in most scenarios.