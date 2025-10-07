# AI Assistance Disclaimer

## AI-Assisted Development

This project was developed with assistance from Claude (Anthropic), an AI assistant. The initial codebase, documentation, and architecture were created through an interactive conversation between a human developer and Claude.

## Nature of AI Contribution

**What Claude helped with:**
- Project structure and architecture design
- Rust code implementation for gRPC client and analysis logic
- Protobuf size estimation calculations
- Documentation (README.md, this disclaimer, metadata files)
- Troubleshooting and refinement based on human feedback

**What the human developer provided:**
- Domain expertise in Zcash protocol
- Specific requirements and constraints
- Protobuf message definitions from actual PRs
- Corrections to initial implementations
- Direction and architectural decisions

## Code Review Required

⚠️ **IMPORTANT**: This code was generated with AI assistance and has NOT been:
- Formally reviewed by Zcash protocol developers
- Tested extensively in production environments
- Audited for correctness of protobuf size calculations
- Validated against actual encoded compact blocks

## Recommendations Before Use

### Required Steps
1. **Review the estimation logic** in `estimate_transparent_overhead()`
   - Verify protobuf encoding calculations
   - Compare estimates against actual encoded sizes
   - Test with known block examples

2. **Validate against real data**
   - Encode test blocks with new fields
   - Compare estimated vs actual sizes
   - Adjust formulas if needed

3. **Test thoroughly**
   - Run on diverse block ranges
   - Verify gRPC client behavior
   - Check error handling

4. **Peer review**
   - Have protocol developers review
   - Validate assumptions about protobuf encoding
   - Confirm decision thresholds are appropriate

### Known Limitations

**Estimation Accuracy**:
- Protobuf varint sizes are approximated
- Nested message overhead may vary slightly
- Actual gRPC compression not accounted for
- Edge cases may not be covered

**Testing Coverage**:
- Limited to the block ranges tested by the user
- May not cover all transaction types
- Network conditions not simulated
- Error paths minimally tested

## Verification Approach

To verify the tool's accuracy:

```bash
# 1. Get actual compact block from lightwalletd
grpcurl -plaintext -d '{"start":{"height":2400000},"end":{"height":2400000}}' \
  localhost:9067 cash.z.wallet.sdk.rpc.CompactTxStreamer/GetBlockRange > current.json

# 2. Manually add transparent data to a copy and encode
# 3. Compare actual size vs. tool's estimate
# 4. Adjust estimation formulas if needed
```

## Use Cases

### ✅ Appropriate Uses
- Protocol design analysis and discussion
- Rough bandwidth impact estimates
- Comparing different design alternatives
- Educational purposes

### ❌ Inappropriate Uses
- Production bandwidth planning without validation
- Final protocol decisions without human review
- Assuming 100% accuracy without verification
- Critical infrastructure without testing

## Continuous Improvement

This tool should be:
- **Validated** against actual implementations
- **Updated** when protocol definitions change
- **Tested** with diverse real-world data
- **Reviewed** by domain experts

## Transparency

We believe in transparent development practices. This disclaimer ensures:
1. Users understand the tool's origins
2. Appropriate skepticism is maintained
3. Proper validation occurs before decisions
4. The community can improve the tool

## Contributing

If you find issues with the estimation logic or have improvements:
1. Test your changes against real data
2. Document your validation approach
3. Submit clear pull requests with rationale
4. Include test cases or block examples

## Acknowledgment

This tool represents a **starting point** for analysis, not a definitive answer. The Zcash community's expertise, testing, and review are essential to making informed protocol decisions.

## Questions?

If you have concerns about:
- Accuracy of size estimates
- Correctness of protobuf encoding
- Architectural decisions
- Testing methodology

Please open an issue or discuss on Zcash community forums. **Do not assume the tool is correct without validation.**

---

**Last Updated**: October 2025  
**AI Model**: Claude (Anthropic)  
**Status**: Initial implementation requiring validation
