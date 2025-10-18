// Medicare Stars Analyzer - Frontend Logic

let currentContract = null;
let measures = [];
let whatIfValues = {};
let allContracts = [];
let selectedContractId = null;

// Load contracts on page load
document.addEventListener('DOMContentLoaded', async () => {
    await loadContracts();
    
    const searchInput = document.getElementById('contractSearch');
    const dropdown = document.getElementById('contractDropdown');
    
    // Show dropdown on focus
    searchInput.addEventListener('focus', () => {
        if (allContracts.length > 0) {
            displayContractOptions(allContracts);
            dropdown.classList.remove('hidden');
        }
    });
    
    // Filter as user types
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        if (query === '') {
            displayContractOptions(allContracts);
        } else {
            const filtered = allContracts.filter(c => 
                c.display.toLowerCase().includes(query) ||
                c.id.toLowerCase().includes(query)
            );
            displayContractOptions(filtered);
        }
        dropdown.classList.remove('hidden');
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.classList.add('hidden');
        }
    });
});

async function loadContracts() {
    try {
        const response = await fetch('/api/contracts');
        const data = await response.json();
        allContracts = data.contracts;
        
        document.getElementById('contractSearch').placeholder = `Search ${allContracts.length} contracts...`;
    } catch (error) {
        console.error('Error loading contracts:', error);
        document.getElementById('contractSearch').placeholder = 'Error loading contracts';
    }
}

function displayContractOptions(contracts) {
    const dropdown = document.getElementById('contractDropdown');
    dropdown.innerHTML = '';
    
    if (contracts.length === 0) {
        dropdown.innerHTML = '<div class="px-4 py-3 text-sm text-gray-500">No contracts found</div>';
        return;
    }
    
    contracts.slice(0, 100).forEach(contract => {
        const div = document.createElement('div');
        div.className = 'px-4 py-3 hover:bg-blue-50 cursor-pointer transition-colors border-b border-gray-100 last:border-0';
        div.innerHTML = `
            <div class="font-medium text-gray-900">${contract.id}</div>
            <div class="text-sm text-gray-600">${contract.marketing_name}</div>
            ${contract.overall_rating ? `<div class="text-xs text-gray-500 mt-1">Overall: ${contract.overall_rating}⭐</div>` : ''}
        `;
        
        div.addEventListener('click', () => {
            selectedContractId = contract.id;
            document.getElementById('contractSearch').value = contract.display;
            document.getElementById('contractDropdown').classList.add('hidden');
            loadContract(contract.id);
        });
        
        dropdown.appendChild(div);
    });
    
    if (contracts.length > 100) {
        const more = document.createElement('div');
        more.className = 'px-4 py-2 text-xs text-gray-500 bg-gray-50 sticky bottom-0';
        more.textContent = `Showing first 100 of ${contracts.length} results. Keep typing to narrow down...`;
        dropdown.appendChild(more);
    }
}

async function loadContract(contractId) {
    try {
        const response = await fetch(`/api/contract/${contractId}`);
        const data = await response.json();
        
        currentContract = data;
        measures = data.measures;
        whatIfValues = {};
        
        // Update UI
        displayContractInfo(data);
        displayMeasures(data.measures);
        calculateMetrics();
        
        // Show hidden elements
        document.getElementById('contractInfo').classList.remove('hidden');
        document.getElementById('metricsBar').classList.remove('hidden');
        document.getElementById('tableContainer').classList.remove('hidden');
    } catch (error) {
        console.error('Error loading contract:', error);
    }
}

function displayContractInfo(data) {
    const info = data.contract_info;
    document.getElementById('contractName').textContent = info.marketing_name;
    document.getElementById('contractOrg').textContent = info.parent_org;
    
    // Only show ratings if they're valid numbers
    const ratings = [];
    if (info.overall_rating && typeof info.overall_rating === 'number') {
        ratings.push(`Overall: ${info.overall_rating}⭐`);
    }
    if (info.part_c_rating && typeof info.part_c_rating === 'number') {
        ratings.push(`Part C: ${info.part_c_rating}⭐`);
    }
    if (info.part_d_rating && typeof info.part_d_rating === 'number') {
        ratings.push(`Part D: ${info.part_d_rating}⭐`);
    }
    
    // Only show ratings if we have at least one
    document.getElementById('contractRatings').innerHTML = ratings.length > 0 
        ? ratings.join(' | ') 
        : '';
}

function displayMeasures(measures) {
    const tbody = document.getElementById('measuresBody');
    tbody.innerHTML = '';
    
    measures.forEach((measure, index) => {
        const row = document.createElement('tr');
        row.className = 'table-row border-b border-gray-100 transition-all';
        
        const inverse = measure.is_inverse ? '* ' : '';
        const starDisplay = measure.star_rating ? `${measure.star_rating}⭐` : '—';
        const riskStatus = calculateRiskStatus(measure);
        const toNext = calculateToNext(measure);
        
        row.innerHTML = `
            <td class="px-4 py-3 text-sm">
                <span class="font-medium text-gray-900">${inverse}${measure.code}:</span>
                <span class="text-gray-600">${measure.name}</span>
            </td>
            <td class="px-4 py-3 text-center text-sm font-medium text-gray-900">${measure.weight}</td>
            <td class="px-4 py-3 text-center text-sm">${starDisplay}</td>
            <td class="px-4 py-3 text-right text-sm font-medium text-gray-900">${measure.performance}</td>
            <td class="px-4 py-3 text-center text-sm text-gray-600">${measure.threshold_band}</td>
            <td class="px-4 py-3 text-center text-sm">${riskStatus}</td>
            <td class="px-4 py-3 text-right text-sm text-gray-600">${toNext}</td>
            <td class="px-4 py-3">
                <input type="number" 
                       class="whatif-input w-24 px-2 py-1 text-sm text-right border border-gray-300 rounded focus:border-blue-500 focus:ring-1 focus:ring-blue-200 outline-none"
                       data-measure="${measure.code}"
                       placeholder="0"
                       step="0.1"
                       min="0"
                       max="100">
            </td>
            <td class="px-4 py-3 text-center text-sm font-medium whatif-star-${measure.code}">—</td>
        `;
        
        tbody.appendChild(row);
    });
    
    // Add event listeners to What-If inputs
    document.querySelectorAll('.whatif-input').forEach(input => {
        input.addEventListener('input', handleWhatIfInput);
    });
}

async function handleWhatIfInput(e) {
    const measureCode = e.target.dataset.measure;
    const value = parseFloat(e.target.value);
    
    if (!value || value === 0) {
        whatIfValues[measureCode] = null;
        document.querySelector(`.whatif-star-${measureCode}`).textContent = '—';
        calculateMetrics();
        return;
    }
    
    try {
        const response = await fetch('/api/whatif', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                measure_code: measureCode,
                value: value,
                contract_id: currentContract.contract_info.contract_id
            })
        });
        
        const data = await response.json();
        whatIfValues[measureCode] = data.star;
        
        const starText = data.star ? `${data.star}⭐` : 'N/A';
        document.querySelector(`.whatif-star-${measureCode}`).textContent = starText;
        
        calculateMetrics();
    } catch (error) {
        console.error('Error calculating what-if:', error);
    }
}

function calculateRiskStatus(measure) {
    if (!measure.performance_numeric) {
        return '<span class="text-gray-400">N/A</span>';
    }
    
    const isInverse = measure.is_inverse;
    const perf = measure.performance_numeric;
    let lower = measure.threshold_lower;
    let upper = measure.threshold_upper;
    
    // Handle open-ended bounds - assume 0 as lower bound for 1-star measures
    if (lower === null && upper !== null) {
        // For 1-star measures with "<X", assume range is 0 to X
        lower = 0;
    }
    
    if (lower !== null && upper === null) {
        // For measures with ">=X" (open upper bound)
        const is5Star = measure.star_rating === 5;
        
        // Special case: if exactly at threshold, it's At Risk (barely made it)
        if (perf === lower) {
            return is5Star 
                ? '<span class="text-red-500">🔴 At Risk</span>'  // 5-star: barely at threshold
                : (isInverse ? '<span class="text-red-500">🔴 At Risk</span>' : '<span class="text-green-500">🟢 Upside</span>');
        }
        
        // Otherwise, assume upper bound and calculate thirds
        const assumedUpper = isInverse ? lower * 2 : 100;  // For inverse, assume 2x threshold; for normal, assume 100%
        upper = assumedUpper;
        measure.assumedUpperBound = true;  // Flag for later use in discrete logic
        
        // Now fall through to normal thirds calculation below
    }
    
    // Need at least upper bound
    if (upper === null) {
        return '<span class="text-gray-400">N/A</span>';
    }
    
    // Check for exact value bands (e.g., "100.0%" where lower == upper)
    const is5Star = measure.star_rating === 5;
    const hasAssumedUpperBound = measure.assumedUpperBound || false;
    if (lower === upper) {
        // Exact value band - always neutral (exactly on target)
        return '<span class="text-yellow-500">🟡 Neutral</span>';
    }
    
    // For 1-value discrete bands, check if performance is within boundaries
    // This handles cases like ">9 to <=10" where 10 is inside the band
    const range = upper - lower;
    if (range > 0.5 && range <= 1) {
        // Check bounds based on measure type:
        // Normal: "88 to <89" → only 88 is valid (exclusive upper)
        // Inverse: ">10 to <=11" → only 11 is valid (exclusive lower)
        let isInside;
        if (isInverse) {
            isInside = perf > lower && perf <= upper;  // Exclusive lower, inclusive upper
        } else {
            isInside = perf >= lower && perf < upper;  // Inclusive lower, exclusive upper
        }
        
        if (isInside) {
            // Inside a 1-value band → Neutral
            return '<span class="text-yellow-500">🟡 Neutral</span>';
        }
        // Otherwise, fall through to outside-band checks
    }
    
    // Check if performance is outside the band
    
    if (perf >= upper) {
        // Performance is above the band
        if (isInverse) {
            return '<span class="text-red-500">🔴 At Risk!</span>';
        } else {
            // For 5-star, can't go higher, so just neutral
            return is5Star 
                ? '<span class="text-yellow-500">🟡 Neutral</span>'
                : '<span class="text-green-500">🟢 Upside!</span>';
        }
    }
    if (perf < lower) {
        // Performance is below the band
        if (isInverse) {
            // For inverse, being below is good
            return is5Star 
                ? '<span class="text-yellow-500">🟡 Neutral</span>'  // 5-star: can't go higher
                : '<span class="text-green-500">🟢 Upside!</span>';
        } else {
            return '<span class="text-red-500">🔴 At Risk!</span>';
        }
    }
    
    // Calculate thirds (only if inside the band)
    // For ranges > 0.5, use discrete (integer) logic; otherwise use continuous (decimal) logic
    // EXCEPTION: 5-star inverse decimals starting at 0 should use discrete logic
    const isSpecialDecimal = isInverse && lower === 0 && range < 1 && is5Star;
    const isDiscrete = range > 0.5 || isSpecialDecimal;
    
    if (isDiscrete) {
        // For inverse measures: lower is EXCLUSIVE (">X"), upper is INCLUSIVE ("<=Y")
        // For normal measures: lower is INCLUSIVE (">=X"), upper is EXCLUSIVE ("<Y")
        let lowerInt, upperInt;
        if (isInverse) {
            // SPECIAL CASE: 5-star inverse decimal starting at 0 (e.g., D02 "≤0.11")
            // Treat as 1-11 (hundredths), not 0-11, since 0 complaints is unrealistic
            if (isSpecialDecimal) {
                lowerInt = 1;  // Start at 0.01 (1 in hundredths)
                upperInt = Math.round(upper * 100);  // 0.11 → 11
            } else if (lower === 0) {
                lowerInt = 0;  // For percentages (e.g., D03 "≤8%"), include 0
                upperInt = Math.floor(upper);  // Inclusive upper
            } else {
                lowerInt = Math.floor(lower) + 1;  // Exclusive: ">10" means starts at 11
                upperInt = Math.floor(upper);       // Inclusive: "<=12" means ends at 12
            }
        } else {
            lowerInt = Math.floor(lower);       // Inclusive: ">=76" means starts at 76
            // For assumed upper bounds (e.g., "86%+"), 100% is achievable (inclusive)
            // For explicit upper bounds (e.g., "<84"), 84% is NOT achievable (exclusive, so use 83)
            upperInt = hasAssumedUpperBound 
                ? Math.floor(upper)         // Inclusive: "86%+" → 86-100
                : Math.floor(upper) - 1;    // Exclusive: "<84" → ends at 83
        }
        const totalValues = upperInt - lowerInt + 1;
        
        // For decimal special case (D02), convert to hundredths; otherwise round normally
        const perfInt = isSpecialDecimal
            ? Math.round(perf * 100)  // D02: 0.08 → 8
            : Math.round(perf);        // D03: 6% → 6, C24: 89 → 89
        
        // If only 1 value, it's Neutral (no way to split)
        if (totalValues <= 1) {
            return '<span class="text-yellow-500">🟡 Neutral</span>';
        }
        
        let position;
        
        // If exactly 2 values, split: first = At Risk, second = Upside
        if (totalValues === 2) {
            position = (perfInt === lowerInt) ? 'lower' : 'upper';
        } else {
            // 3+ values: Split into thirds (remainder goes to middle)
            // 9→3,3,3 | 8→2,4,2 | 7→2,3,2 | 11→3,5,3 | 15→5,5,5
            const outerThirdSize = Math.floor(totalValues / 3);
            const firstThirdEnd = lowerInt + outerThirdSize - 1;
            const lastThirdStart = upperInt - outerThirdSize + 1;
            
            if (perfInt <= firstThirdEnd) position = 'lower';
            else if (perfInt >= lastThirdStart) position = 'upper';
            else position = 'middle';
        }
        
        // For 5-star, there is no upside (can't go higher than 5)
        if (isInverse) {
            if (position === 'lower') {
                return is5Star 
                    ? '<span class="text-yellow-500">🟡 Neutral</span>' 
                    : '<span class="text-green-500">🟢 Upside</span>';
            }
            if (position === 'upper') return '<span class="text-red-500">🔴 At Risk</span>';
        } else {
            if (position === 'lower') return '<span class="text-red-500">🔴 At Risk</span>';
            if (position === 'upper') {
                return is5Star 
                    ? '<span class="text-yellow-500">🟡 Neutral</span>' 
                    : '<span class="text-green-500">🟢 Upside</span>';
            }
        }
        return '<span class="text-yellow-500">🟡 Neutral</span>';
    } else {
        // For decimals/continuous ranges (e.g., 0.11 to 0.32)
        // Use strict inequality so boundary values go to middle (tie-to-middle)
        const range = upper - lower;
        const third = range / 3.0;
        const lowerThirdEnd = lower + third;
        const upperThirdStart = upper - third;
        
        let position;
        if (perf < lowerThirdEnd) position = 'lower';
        else if (perf > upperThirdStart) position = 'upper';
        else position = 'middle';
        
        // For 5-star, there is no upside (can't go higher than 5)
        if (isInverse) {
            if (position === 'lower') {
                return is5Star 
                    ? '<span class="text-yellow-500">🟡 Neutral</span>' 
                    : '<span class="text-green-500">🟢 Upside</span>';
            }
            if (position === 'upper') return '<span class="text-red-500">🔴 At Risk</span>';
        } else {
            if (position === 'lower') return '<span class="text-red-500">🔴 At Risk</span>';
            if (position === 'upper') {
                return is5Star 
                    ? '<span class="text-yellow-500">🟡 Neutral</span>' 
                    : '<span class="text-green-500">🟢 Upside</span>';
            }
        }
        return '<span class="text-yellow-500">🟡 Neutral</span>';
    }
}

function calculateToNext(measure) {
    if (measure.star_rating === 5) {
        return 'Already at 5⭐';
    }
    
    if (!measure.performance_numeric || measure.threshold_upper === null) {
        return 'N/A';
    }
    
    const gap = measure.threshold_upper - measure.performance_numeric;
    
    if (gap <= 0) {
        return 'At threshold';
    }
    
    if (measure.format_type === 'PERCENTAGE') {
        return `${gap.toFixed(1)}%`;
    } else if (measure.format_type === 'INTEGER') {
        return `${Math.floor(gap)}`;
    } else if (measure.format_type === 'DECIMAL') {
        return `${gap.toFixed(2)}`;
    }
    
    return `${gap.toFixed(1)}`;
}

function calculateMetrics() {
    let weightedSum = 0;
    let totalWeight = 0;
    let whatifWeightedSum = 0;
    let whatifTotalWeight = 0;
    let riskScore = 0;
    
    measures.forEach(measure => {
        if (measure.star_rating) {
            weightedSum += measure.star_rating * measure.weight;
            totalWeight += measure.weight;
        }
        
        // What-If calculation
        const whatifStar = whatIfValues[measure.code];
        const starToUse = whatifStar || measure.star_rating;
        
        if (starToUse) {
            whatifWeightedSum += starToUse * measure.weight;
            whatifTotalWeight += measure.weight;
        }
        
        // Risk score
        const riskStatus = calculateRiskStatus(measure);
        if (riskStatus.includes('At Risk')) {
            riskScore -= measure.weight;
        } else if (riskStatus.includes('Upside')) {
            riskScore += measure.weight;
        }
    });
    
    const weightedAvg = totalWeight > 0 ? (weightedSum / totalWeight).toFixed(2) : '0.00';
    const whatifAvg = whatifTotalWeight > 0 ? (whatifWeightedSum / whatifTotalWeight).toFixed(2) : '0.00';
    
    document.getElementById('weightedAvg').textContent = `${weightedAvg}⭐`;
    document.getElementById('whatifAvg').textContent = `${whatifAvg}⭐`;
    document.getElementById('riskScore').textContent = riskScore >= 0 ? `+${riskScore.toFixed(1)}` : riskScore.toFixed(1);
}

