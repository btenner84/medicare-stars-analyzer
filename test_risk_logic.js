// Test script for 5-star "no upside" risk logic

// Mock the calculateRiskStatus function logic
function testRiskStatus(scenario, measure, expected) {
    const { perf, lower, upper, star, isInverse } = measure;
    const is5Star = star === 5;
    
    let result;
    
    // Open upper bound (e.g., ">=99%")
    if (lower !== null && upper === null) {
        if (perf === lower) {
            result = is5Star ? '🔴 At Risk' : (isInverse ? '🔴 At Risk' : '🟢 Upside');
        } else {
            result = is5Star ? '🟡 Neutral' : (isInverse ? '🔴 At Risk' : '🟢 Upside');
        }
    }
    // Exact value band (e.g., "100%")
    else if (lower === upper) {
        result = '🟡 Neutral';
    }
    // 1-value discrete band - check if performance is within boundaries
    else if ((upper - lower) > 0.5 && (upper - lower) <= 1) {
        let isInside;
        if (isInverse) {
            isInside = perf > lower && perf <= upper;  // Exclusive lower, inclusive upper
        } else {
            isInside = perf >= lower && perf < upper;  // Inclusive lower, exclusive upper
        }
        if (isInside) {
            result = '🟡 Neutral';  // Inside 1-value band
        }
        // Otherwise fall through to outside-band checks
    }
    // Outside band (above)
    if (perf >= upper && result === undefined) {
        if (isInverse) {
            result = '🔴 At Risk!';
        } else {
            result = is5Star ? '🟡 Neutral' : '🟢 Upside!';
        }
    }
    // Outside band (below)
    if (perf < lower && result === undefined) {
        if (isInverse) {
            result = is5Star ? '🟡 Neutral' : '🟢 Upside!';
        } else {
            result = '🔴 At Risk!';
        }
    }
    // Inside band - discrete logic
    if (result === undefined) {
        const range = upper - lower;
        if (range > 0.5) {
            // Discrete - handle inverse vs normal bounds
            let lowerInt, upperInt;
            if (isInverse) {
                lowerInt = Math.floor(lower) + 1;  // Exclusive: ">10" → starts at 11
                upperInt = Math.floor(upper);       // Inclusive: "<=12" → ends at 12
            } else {
                lowerInt = Math.floor(lower);       // Inclusive: ">=76" → starts at 76
                upperInt = Math.floor(upper) - 1;   // Exclusive: "<84" → ends at 83
            }
            const totalValues = upperInt - lowerInt + 1;
            const perfInt = Math.round(perf);
            
            let position;
            if (totalValues <= 1) {
                result = '🟡 Neutral';
            } else if (totalValues === 2) {
                position = (perfInt === lowerInt) ? 'lower' : 'upper';
            } else {
                const thirdSize = Math.floor(totalValues / 3);
                const firstThirdEnd = lowerInt + thirdSize - 1;
                const lastThirdStart = upperInt - thirdSize + 1;
                
                if (perfInt <= firstThirdEnd) position = 'lower';
                else if (perfInt >= lastThirdStart) position = 'upper';
                else position = 'middle';
            }
            
            // Apply inverse logic for discrete
            if (isInverse) {
                if (position === 'lower') {
                    result = is5Star ? '🟡 Neutral' : '🟢 Upside';
                } else if (position === 'upper') {
                    result = '🔴 At Risk';
                } else {
                    result = '🟡 Neutral';
                }
            } else {
                if (position === 'lower') {
                    result = '🔴 At Risk';
                } else if (position === 'upper') {
                    result = is5Star ? '🟡 Neutral' : '🟢 Upside';
                } else {
                    result = '🟡 Neutral';
                }
            }
        } else {
            // Continuous (decimals)
            const third = range / 3.0;
            const lowerThirdEnd = lower + third;
            const upperThirdStart = upper - third;
            
            let position;
            if (perf <= lowerThirdEnd) position = 'lower';
            else if (perf >= upperThirdStart) position = 'upper';
            else position = 'middle';
            
            // Apply inverse logic for continuous
            if (isInverse) {
                if (position === 'lower') {
                    result = is5Star ? '🟡 Neutral' : '🟢 Upside';
                } else if (position === 'upper') {
                    result = '🔴 At Risk';
                } else {
                    result = '🟡 Neutral';
                }
            } else {
                if (position === 'lower') {
                    result = '🔴 At Risk';
                } else if (position === 'upper') {
                    result = is5Star ? '🟡 Neutral' : '🟢 Upside';
                } else {
                    result = '🟡 Neutral';
                }
            }
        }
    }
    
    const pass = result === expected;
    console.log(`${pass ? '✅' : '❌'} ${scenario}`);
    console.log(`   Input: perf=${perf}, band=[${lower}, ${upper}], star=${star}, inverse=${isInverse}`);
    console.log(`   Expected: ${expected}`);
    console.log(`   Got:      ${result}`);
    if (!pass) console.log(`   ⚠️  FAILED!`);
    console.log('');
    
    return pass;
}

console.log('=== Testing 5-Star "No Upside" Logic ===\n');

let passed = 0;
let failed = 0;

// Test 1: 5-star with open upper bound (e.g., "99%+")
if (testRiskStatus(
    'Test 1: 5⭐ at threshold (99% in "99%+")',
    { perf: 99, lower: 99, upper: null, star: 5, isInverse: false },
    '🔴 At Risk'
)) passed++; else failed++;

if (testRiskStatus(
    'Test 2: 5⭐ above threshold (100% in "99%+")',
    { perf: 100, lower: 99, upper: null, star: 5, isInverse: false },
    '🟡 Neutral'
)) passed++; else failed++;

// Test 3: 5-star with exact value band (e.g., "100%")
if (testRiskStatus(
    'Test 3: 5⭐ exact value (100% in "100%")',
    { perf: 100, lower: 100, upper: 100, star: 5, isInverse: false },
    '🟡 Neutral'
)) passed++; else failed++;

// Test 4: 5-star with range band - lower third
if (testRiskStatus(
    'Test 4: 5⭐ lower third (95% in "95-100%")',
    { perf: 95, lower: 95, upper: 100, star: 5, isInverse: false },
    '🔴 At Risk'
)) passed++; else failed++;

// Test 5: 5-star with range band - upper third (should be Neutral, not Upside)
if (testRiskStatus(
    'Test 5: 5⭐ upper third (99% in "95-100%")',
    { perf: 99, lower: 95, upper: 100, star: 5, isInverse: false },
    '🟡 Neutral'
)) passed++; else failed++;

// Test 6: 4-star should still have Upside
if (testRiskStatus(
    'Test 6: 4⭐ upper third (84% in "76-84%")',
    { perf: 83, lower: 76, upper: 84, star: 4, isInverse: false },
    '🟢 Upside'
)) passed++; else failed++;

// Test 7: 5-star above band (e.g., 101% in "95-100%")
if (testRiskStatus(
    'Test 7: 5⭐ above band (101% in "95-100%")',
    { perf: 101, lower: 95, upper: 100, star: 5, isInverse: false },
    '🟡 Neutral'
)) passed++; else failed++;

// Test 8: 4-star above band (should be Upside!)
if (testRiskStatus(
    'Test 8: 4⭐ above band (85% in "76-84%")',
    { perf: 85, lower: 76, upper: 84, star: 4, isInverse: false },
    '🟢 Upside!'
)) passed++; else failed++;

// Test 9: 5-star inverse measure - lower is better
if (testRiskStatus(
    'Test 9: 5⭐ inverse lower third (0.10 in "0.10-0.20")',
    { perf: 0.10, lower: 0.10, upper: 0.20, star: 5, isInverse: true },
    '🟡 Neutral'
)) passed++; else failed++;

// Test 10: 5-star inverse below band (even better)
if (testRiskStatus(
    'Test 10: 5⭐ inverse below band (0.08 in "0.10-0.20")',
    { perf: 0.08, lower: 0.10, upper: 0.20, star: 5, isInverse: true },
    '🟡 Neutral'
)) passed++; else failed++;

// Test 11: Single value band at 5-star
if (testRiskStatus(
    'Test 11: 5⭐ single value (90% in "90-91%")',
    { perf: 90, lower: 90, upper: 91, star: 5, isInverse: false },
    '🟡 Neutral'
)) passed++; else failed++;

// Test 12: Two value band at 5-star - first value
if (testRiskStatus(
    'Test 12: 5⭐ two-value lower (88% in "88-90%")',
    { perf: 88, lower: 88, upper: 90, star: 5, isInverse: false },
    '🔴 At Risk'
)) passed++; else failed++;

// Test 13: Two value band at 5-star - second value
if (testRiskStatus(
    'Test 13: 5⭐ two-value upper (89% in "88-90%")',
    { perf: 89, lower: 88, upper: 90, star: 5, isInverse: false },
    '🟡 Neutral'
)) passed++; else failed++;

// Test 14: Performance OUTSIDE 1-value band (D05 scenario)
if (testRiskStatus(
    'Test 14: 2⭐ above 1-value band (87 in "85-86")',
    { perf: 87, lower: 85, upper: 86, star: 2, isInverse: false },
    '🟢 Upside!'
)) passed++; else failed++;

// Test 15: Performance INSIDE 1-value band (C18 scenario)
if (testRiskStatus(
    'Test 15: 3⭐ inverse 1-value band (10% in ">9-10%")',
    { perf: 10, lower: 9, upper: 10, star: 3, isInverse: true },
    '🟡 Neutral'
)) passed++; else failed++;

// Test 16: C18 inverse 2-value band - lower value (better)
if (testRiskStatus(
    'Test 16: 2⭐ inverse 2-value lower (11% in ">10-12%")',
    { perf: 11, lower: 10, upper: 12, star: 2, isInverse: true },
    '🟢 Upside'
)) passed++; else failed++;

// Test 17: C18 inverse 2-value band - upper value (worse)
if (testRiskStatus(
    'Test 17: 2⭐ inverse 2-value upper (12% in ">10-12%")',
    { perf: 12, lower: 10, upper: 12, star: 2, isInverse: true },
    '🔴 At Risk'
)) passed++; else failed++;

// Test 18: C24 normal 1-value band - performance OUTSIDE (above)
if (testRiskStatus(
    'Test 18: 2⭐ above 1-value band (89 in "88 to <89")',
    { perf: 89, lower: 88, upper: 89, star: 2, isInverse: false },
    '🟢 Upside!'
)) passed++; else failed++;

// Test 19: Normal 1-value band - performance INSIDE
if (testRiskStatus(
    'Test 19: 2⭐ inside 1-value band (88 in "88 to <89")',
    { perf: 88, lower: 88, upper: 89, star: 2, isInverse: false },
    '🟡 Neutral'
)) passed++; else failed++;

console.log('=== Summary ===');
console.log(`✅ Passed: ${passed}`);
console.log(`❌ Failed: ${failed}`);
console.log(`Total: ${passed + failed}`);

process.exit(failed > 0 ? 1 : 0);

