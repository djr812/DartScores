// Darts Scoring System - Frontend JavaScript
class DartsGame {
    constructor() {
        this.currentMatchId = null;
        this.currentLegId = null;
        this.currentPlayerId = null;
        this.currentDartNumber = 1;
        this.currentMultiplier = 1;
        this.currentTurnIsBust = false;
        this.players = [];
        this.offlineThrows = [];
        this.isOnline = true;
        
        this.init();
    }
    
    init() {
        console.log('=== DartsGame.init() called ===');
        
        // Check if DOM is ready
        if (document.readyState === 'loading') {
            console.log('DOM still loading, waiting...');
            document.addEventListener('DOMContentLoaded', () => {
                console.log('DOMContentLoaded fired, continuing init...');
                this.continueInit();
            });
        } else {
            console.log('DOM already loaded, continuing init...');
            this.continueInit();
        }
    } 
    
    continueInit() {
        console.log('=== continueInit called ===');
        
        this.bindEvents();
        this.loadPlayers();
        this.checkConnection();
        this.setupSegmentGrid();
        
        // Log initial state
        this.logGameState('init');
        
        // Check for active game
        this.findAndUseLatestMatch();
        
        // Set up periodic connection check
        setInterval(() => this.checkConnection(), 5000);
        
        console.log('Initialization complete');
    }
        bindEvents() {
            console.log('=== bindEvents called ===');
    
            // Helper function to safely bind events
            const safeBind = (elementId, eventName, handler) => {
                const element = document.getElementById(elementId);
                if (element) {
                    console.log(`Binding ${eventName} to ${elementId}`);
                    element.addEventListener(eventName, handler);
                } else {
                    console.error(`Element ${elementId} not found for event binding`);
                }
            };

        // Multiplier buttons
        console.log('Binding multiplier buttons...');
        document.querySelectorAll('.multiplier-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.multiplier-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.currentMultiplier = parseInt(e.target.dataset.multiplier);
                console.log(`Multiplier set to: ${this.currentMultiplier}`);
            });
        });
        
        // Special buttons (Bull/Double Bull)
        safeBind('bull-btn', 'click', () => {
            console.log('Bull button clicked');
            this.recordThrow(25, 1);
        });
        
        safeBind('double-bull-btn', 'click', () => {
            console.log('Double bull button clicked');
            this.recordThrow(25, 2);
        });
        
        // Control buttons
        safeBind('undo-btn', 'click', () => this.undoLastThrow());
        safeBind('next-player-btn', 'click', () => this.nextPlayer());
        safeBind('new-game-btn', 'click', () => this.showNewGameModal());
        safeBind('stats-btn', 'click', () => this.showStatsModal());
        safeBind('refresh-btn', 'click', () => this.forceRefreshGame());
        
        // Modal buttons
        safeBind('start-game-btn', 'click', () => this.startNewGame());
        safeBind('cancel-game-btn', 'click', () => this.hideModal('new-game-modal'));
        safeBind('close-stats-btn', 'click', () => this.hideModal('stats-modal'));
    
        // Click outside modal to close
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.hideModal(modal.id);
                }
            });
        });
        console.log('Event binding complete');
    }
    
    setupSegmentGrid() {
        console.log('=== setupSegmentGrid called ===');

        const grid = document.getElementById('segment-grid');
        console.log('Found segment-grid element:', grid);

        if (!grid) {
            console.error('segment-grid element not found');
            console.error('Available elements with id:');
            const allElements = document.querySelectorAll('[id]');
            allElements.forEach(el => console.log(`  ${el.id}`));
            return;
        }
        
        console.log('Clearing grid...');
        grid.innerHTML = '';
        
        // Create buttons for segments 1-20
        console.log('Creating segment buttons...');
        for (let segment = 1; segment <= 20; segment++) {
            const btn = document.createElement('button');
            btn.className = 'segment-btn';
            btn.textContent = segment;
            btn.dataset.segment = segment;
            btn.addEventListener('click', () => {
                console.log(`Segment ${segment} clicked, multiplier ${this.currentMultiplier}`);
                this.recordThrow(segment, this.currentMultiplier);
            });
            grid.appendChild(btn);
        }
        
        // Add miss button (segment 0)
        console.log('Creating miss button...');
        const missBtn = document.createElement('button');
        missBtn.className = 'segment-btn bull';
        missBtn.textContent = 'Miss (0)';
        missBtn.dataset.segment = '0';
        missBtn.addEventListener('click', () => {
            console.log('Miss button clicked');
            this.recordThrow(0, 0);
        });
        grid.appendChild(missBtn);

        console.log(`Created ${grid.children.length} buttons in segment-grid`);
    }
        logGameState(context = '') {
        console.log(`=== Game State ${context} ===`);
        console.log(`Match ID: ${this.currentMatchId} (type: ${typeof this.currentMatchId})`);
        console.log(`Leg ID: ${this.currentLegId} (type: ${typeof this.currentLegId})`);
        console.log(`Player ID: ${this.currentPlayerId} (type: ${typeof this.currentPlayerId})`);
        console.log(`Dart Number: ${this.currentDartNumber} (type: ${typeof this.currentDartNumber})`);
        console.log(`Is Online: ${this.isOnline}`);
        console.log(`Offline Throws: ${this.offlineThrows.length}`);
        console.log(`====================`);
    }
    
    async findAndUseLatestMatch() {
        console.log('Finding latest active match...');
        
        try {
            const response = await this.apiRequest('/api/matches?status=active');
            const matches = response.matches;
            
            if (matches && matches.length > 0) {
                // Find the most recent match (highest ID)
                const latestMatch = matches.reduce((latest, current) => {
                    return current.id > latest.id ? current : latest;
                });
                
                console.log(`Found latest match: ${latestMatch.id}`);
                
                // Get the current leg for this match
                const legResponse = await this.apiRequest(`/api/matches/${latestMatch.id}/legs/current`);
                
                // Update game state
                this.currentMatchId = latestMatch.id;
                this.currentLegId = legResponse.leg.id;
                this.currentPlayerId = legResponse.current_player_id;
                
                // Set dart number
                if (legResponse.current_turn && legResponse.current_turn.throws) {
                    const throws = legResponse.current_turn.throws;
                    this.currentDartNumber = throws.length + 1;
                    
                    // Ensure dart number is valid
                    if (this.currentDartNumber > 3 || this.currentDartNumber < 1) {
                        this.currentDartNumber = 1;
                    }
                } else {
                    this.currentDartNumber = 1;
                }
                
                console.log(`Updated to match ${this.currentMatchId}, leg ${this.currentLegId}, dart ${this.currentDartNumber}`);
                
                // Update display
                this.updateGameDisplay(legResponse);
                
                return true;
            } else {
                console.log('No active matches found');
                this.resetGameState();
                return false;
            }
            
        } catch (error) {
            console.error('Failed to find latest match:', error);
            this.resetGameState();
            return false;
        }
    }
    
    async loadGameState() {
        console.log('=== loadGameState called ===');
        
        if (!this.currentMatchId) {
            console.log('No current match ID');
            return;
        }
        
        console.log(`Loading game state for match ${this.currentMatchId}`);
        
        try {
            const response = await this.apiRequest(`/api/matches/${this.currentMatchId}/legs/current`);
            console.log('Game state loaded:', response);
            
            // Update IDs from response
            this.currentLegId = response.leg.id;
            this.currentPlayerId = response.current_player_id;
            
            // Update dart number based on current turn
            // IMPORTANT: Don't auto-reset when turn is complete
            if (response.current_turn && response.current_turn.throws) {
                const throws = response.current_turn.throws;
                this.currentDartNumber = throws.length + 1;
                
                // Check if turn is complete (3 darts or bust)
                const isTurnComplete = throws.length >= 3 || response.current_turn.is_bust;
                
                if (isTurnComplete) {
                    // Turn is complete - keep dart number > 3 to disable buttons
                    // Don't reset to 1 automatically
                    console.log(`Turn complete (${throws.length} darts, bust: ${response.current_turn.is_bust})`);
                    this.currentTurnIsBust = response.current_turn.is_bust;
                } else {
                    // Turn in progress
                    this.currentTurnIsBust = false;
                    console.log(`Current turn has ${throws.length} throws, dart number: ${this.currentDartNumber}`);
                }
            } else {
                // No current turn (just started or after next player)
                this.currentDartNumber = 1;
                this.currentTurnIsBust = false;
                console.log('No current turn, starting with dart 1');
            }
            
            this.updateGameDisplay(response);
            
            // Update button states
            this.updateButtonStates();
            
        } catch (error) {
            console.error('Failed to load game state:', error);
            
            if (error.message.includes('404')) {
                console.log('Game not found, resetting state');
                this.resetGameState();
                this.showError('Game not found. Please start a new game.');
            }
        }
    }

    updateTurnStatus() {
        const turnStatus = document.getElementById('turn-status');
        const dartsRemaining = document.getElementById('darts-remaining');
        
        if (!turnStatus || !dartsRemaining) return;
        
        if (this.currentDartNumber > 3 || this.currentTurnIsBust) {
            // Turn complete
            turnStatus.className = 'turn-status complete';
            if (this.currentTurnIsBust) {
                dartsRemaining.textContent = 'BUST! Tap Next Player';
            } else {
                dartsRemaining.textContent = 'Turn Complete! Tap Next Player';
            }
        } else {
            // Turn in progress
            turnStatus.className = 'turn-status';
            const remaining = 4 - this.currentDartNumber;
            dartsRemaining.textContent = `${remaining} dart${remaining !== 1 ? 's' : ''} remaining`;
        }
    }

        async loadPlayers() {
        try {
            const response = await this.apiRequest('/api/players');
            this.players = response.players;
            this.updatePlayerSelection();
        } catch (error) {
            console.error('Failed to load players:', error);
            this.showError('Failed to load players. Please check connection.');
        }
    }
    
    updatePlayerSelection() {
        const container = document.getElementById('player-selection');
        if (!container) return;
        
        container.innerHTML = '';
        
        this.players.forEach(player => {
            const div = document.createElement('div');
            div.className = 'player-option';
            
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = `player-${player.id}`;
            checkbox.value = player.id;
            checkbox.checked = true;
            
            const label = document.createElement('label');
            label.htmlFor = `player-${player.id}`;
            label.textContent = player.nickname || player.name;
            
            div.appendChild(checkbox);
            div.appendChild(label);
            container.appendChild(div);
        });
    }
    
    updateGameDisplay(gameState) {
        // Update game info
        document.getElementById('game-type').textContent = gameState.game_type;
        document.getElementById('remaining-score').textContent = gameState.leg.remaining_score || 501;
        
        // Update player scores
        const scoresContainer = document.getElementById('player-scores');
        scoresContainer.innerHTML = '';
        
        gameState.players.forEach(player => {
            const playerDiv = document.createElement('div');
            playerDiv.className = 'player-score';
            if (player.id === this.currentPlayerId) {
                playerDiv.classList.add('active');
                document.getElementById('current-player').textContent = player.nickname || player.name;
            }
            
            // Calculate player's current score
            const playerTurns = gameState.turns.filter(turn => turn.player_id === player.id);
            const totalScore = playerTurns.reduce((sum, turn) => sum + turn.score, 0);
            const remaining = 501 - totalScore;
            
            playerDiv.innerHTML = `
                <div class="player-name">${player.nickname || player.name}</div>
                <div class="player-total">${remaining}</div>
            `;
            
            scoresContainer.appendChild(playerDiv);
        });
        
        // Update dart throws display
        const currentTurn = gameState.current_turn;
        const dartThrows = document.getElementById('dart-throws');
        
        if (currentTurn && currentTurn.throws) {
            currentTurn.throws.forEach(throwObj => {
                const dartElement = dartThrows.children[throwObj.dart_number - 1];
                const multiplierText = throwObj.multiplier === 1 ? '' : 
                                     throwObj.multiplier === 2 ? 'D' : 'T';
                dartElement.textContent = `${throwObj.dart_number}: ${multiplierText}${throwObj.segment} (${throwObj.points})`;
            });
            
            // Update turn total
            const turnTotal = currentTurn.throws.reduce((sum, t) => sum + t.points, 0);
            document.getElementById('turn-total').textContent = `Turn: ${turnTotal}`;
        } else {
            // Reset dart display
            for (let i = 0; i < 3; i++) {
                dartThrows.children[i].textContent = `${i + 1}: `;
            }
            document.getElementById('turn-total').textContent = 'Turn: 0';
        }
        
        // Update button states
        this.updateButtonStates();
        this.updateTurnStatus();
    }

    async recordThrow(segment, multiplier) {
        console.log(`=== recordThrow ===`);
        this.logGameState('before throw');
        
        // VALIDATE DART NUMBER - CRITICAL FIX
        if (typeof this.currentDartNumber !== 'number' || isNaN(this.currentDartNumber)) {
            console.error('Invalid dart number detected, resetting to 1');
            this.currentDartNumber = 1;
        }
        
        if (this.currentDartNumber < 1 || this.currentDartNumber > 3) {
            console.error(`Dart number out of range: ${this.currentDartNumber}, resetting to 1`);
            this.currentDartNumber = 1;
        }
        
        console.log(`Attempting dart ${this.currentDartNumber}, segment ${segment}, multiplier ${multiplier}`);
        
        if (!this.currentMatchId || !this.currentLegId || !this.currentPlayerId) {
            this.showError('No active game. Please start a new game.');
            return;
        }
        
        const throwData = {
            player_id: this.currentPlayerId,
            segment: segment,
            multiplier: multiplier,
            dart_number: this.currentDartNumber
        };
        
        console.log('Throw data:', throwData);
        
        try {
            const response = await this.apiRequest(
                `/api/matches/${this.currentMatchId}/legs/${this.currentLegId}/throw`,
                'POST',
                throwData
            );
            
            console.log('Throw successful - FULL RESPONSE:', JSON.stringify(response, null, 2));
            
            // Check what's in the response
            console.log('Response analysis:');
            console.log('  Has turn object?', 'turn' in response);
            console.log('  Turn ID:', response.turn?.id);
            console.log('  Darts thrown:', response.turn?.darts_thrown);
            console.log('  Is bust?', response.is_bust);
            console.log('  Is checkout?', response.is_checkout);
            console.log('  Game completed?', response.game_completed);
            
            // ========== BUST HANDLING ==========
            if (response.is_bust) {
                console.log('BUST detected!');
                this.showMessage('Bust! Score reverts. Next player.');

                // Bust means turn is complete immediately
                this.currentDartNumber = 1;
                this.currentTurnIsBust = true; // Track bust state
                
                // Update UI to show bust
                this.updateUIForBust(response, segment, multiplier);
                
            } else if (response.game_completed) {
                console.log('GAME COMPLETED! Checkout!');
                this.showMessage(`Game won! Checkout: ${response.throw.points}`);
                this.currentDartNumber = 1;
                this.currentTurnIsBust = false;
                
                // Update UI for checkout
                this.updateUIAfterThrow(response, segment, multiplier);
                
            } else {
                this.currentTurnIsBust = false; // Reset bust state
                // Normal throw - update dart number
                this.currentDartNumber++;
                
                // If we've thrown 3 darts, reset for next turn
                if (this.currentDartNumber > 3) {
                    console.log('3 darts thrown - turn complete (waiting for Next Player)');
                    this.showMessage('Turn complete. Tap Next Player.');
                }
                
                console.log(`Updated dart number to: ${this.currentDartNumber}`);
                
                // Update UI for normal throw
                this.updateUIAfterThrow(response, segment, multiplier);
            }
            
            // Update button states after throw
            this.updateButtonStates();

            // Refresh game state from server
            await this.loadGameState();
            
        } catch (error) {
            console.error('Throw failed:', error);
            this.showError('Throw failed. Please check game state.');
            await this.loadGameState();
        }
        }
        
        updateUIAfterThrow(response, segment, multiplier) {
        console.log('Updating UI after throw...');
        
        // Update dart display
        const dartThrows = document.getElementById('dart-throws');
        if (dartThrows && response.throw) {
            const throwObj = response.throw;
            const dartIndex = throwObj.dart_number - 1;
            
            if (dartIndex >= 0 && dartIndex < 3) {
                const dartElement = dartThrows.children[dartIndex];
                const multiplierText = throwObj.multiplier === 1 ? '' : 
                                    throwObj.multiplier === 2 ? 'D' : 'T';
                dartElement.textContent = `${throwObj.dart_number}: ${multiplierText}${throwObj.segment} (${throwObj.points})`;
            }
        }
        
        // Update turn total
        if (response.turn) {
            document.getElementById('turn-total').textContent = `Turn: ${response.turn.score}`;
        }
        
        // Update remaining score
        if (response.remaining_score !== undefined) {
            document.getElementById('remaining-score').textContent = response.remaining_score;
        }
    }

    updateUIForBust(response, segment, multiplier) {
        console.log('Updating UI for bust...');
        
        // Update dart display with BUST indicator
        const dartThrows = document.getElementById('dart-throws');
        if (dartThrows && response.throw) {
            const throwObj = response.throw;
            const dartIndex = throwObj.dart_number - 1;
            
            if (dartIndex >= 0 && dartIndex < 3) {
                const dartElement = dartThrows.children[dartIndex];
                const multiplierText = throwObj.multiplier === 1 ? '' : 
                                    throwObj.multiplier === 2 ? 'D' : 'T';
                
                // Add BUST! to the display
                dartElement.textContent = `${throwObj.dart_number}: ${multiplierText}${throwObj.segment} (${throwObj.points}) BUST!`;
                dartElement.style.color = '#e94560';
                dartElement.style.fontWeight = 'bold';
            }
        }
        
        // Update turn total to show BUST
        const turnTotalElement = document.getElementById('turn-total');
        turnTotalElement.textContent = 'Turn: BUST!';
        turnTotalElement.style.color = '#e94560';
        turnTotalElement.style.fontWeight = 'bold';
        
        // Update remaining score (should stay the same after bust)
        if (response.remaining_score !== undefined) {
            document.getElementById('remaining-score').textContent = response.remaining_score;
        }
        
        // Clear the bust display after 2 seconds
        setTimeout(() => {
            this.clearBustDisplay();
        }, 2000);
    }

    clearBustDisplay() {
        console.log('Clearing bust display...');
        
        // Reset dart display colors
        const dartThrows = document.getElementById('dart-throws');
        if (dartThrows) {
            for (let i = 0; i < 3; i++) {
                const dartElement = dartThrows.children[i];
                dartElement.style.color = '';
                dartElement.style.fontWeight = '';
            }
        }
        
        // Reset turn total display
        const turnTotalElement = document.getElementById('turn-total');
        if (turnTotalElement) {
            turnTotalElement.textContent = 'Turn: 0';
            turnTotalElement.style.color = '';
            turnTotalElement.style.fontWeight = '';
        }
    }

    calculatePoints(segment, multiplier) {
        if (segment === 0) return 0;
        if (segment === 25) return multiplier === 2 ? 50 : 25;
        return segment * multiplier;
    }
        async undoLastThrow() {
        if (!this.currentMatchId || !this.currentLegId) {
            this.showError('No active game.');
            return;
        }
        
        try {
            const response = await this.apiRequest(
                `/api/matches/${this.currentMatchId}/legs/${this.currentLegId}/undo`,
                'POST'
            );
            
            // Reload game state
            await this.loadGameState();
            this.showMessage('Last throw undone.');
        } catch (error) {
            console.error('Failed to undo throw:', error);
            this.showError('Failed to undo throw.');
        }
    }
    
        async nextPlayer() {
        if (!this.currentMatchId || !this.currentLegId) {
            this.showError('No active game.');
            return;
        }
        
        try {
            const response = await this.apiRequest(
                `/api/matches/${this.currentMatchId}/legs/${this.currentLegId}/next-player`,
                'POST'
            );
            
            this.currentPlayerId = response.next_player_id;
            this.currentDartNumber = 1;  // Reset to dart 1
            this.currentTurnIsBust = false;  // Reset bust state
            
            console.log(`Switched to player ${this.currentPlayerId}, dart ${this.currentDartNumber}`);
            
            // Clear dart display
            const dartThrows = document.getElementById('dart-throws');
            if (dartThrows) {
                for (let i = 0; i < 3; i++) {
                    dartThrows.children[i].textContent = `${i + 1}: `;
                    dartThrows.children[i].style.color = '';
                    dartThrows.children[i].style.fontWeight = '';
                }
            }
            
            // Reset turn total display
            const turnTotalElement = document.getElementById('turn-total');
            if (turnTotalElement) {
                turnTotalElement.textContent = 'Turn: 0';
                turnTotalElement.style.color = '';
                turnTotalElement.style.fontWeight = '';
            }
            
            // Update button states (re-enable throw buttons)
            this.updateButtonStates();
            
            // Update display
            await this.loadGameState();
            
            // Show message
            this.showMessage(`Now playing: Player ${this.currentPlayerId}`);
            
        } catch (error) {
            console.error('Failed to switch player:', error);
            this.showError('Failed to switch player.');
        }
    }
    
    showNewGameModal() {
        this.updatePlayerSelection();
        this.showModal('new-game-modal');
    }
    
    async startNewGame() {
        const selectedPlayers = Array.from(
            document.querySelectorAll('#player-selection input:checked')
        ).map(input => parseInt(input.value));
        
        if (selectedPlayers.length < 2) {
            this.showError('Please select at least 2 players.');
            return;
        }
        
        try {
            console.log('Creating new game with players:', selectedPlayers);
            
            const response = await this.apiRequest('/api/matches', 'POST', {
                player_ids: selectedPlayers,
                game_type: '501'
            });
            
            console.log('New game created:', response);
            
            // CRITICAL: Make sure we're using the right IDs
            this.currentMatchId = response.match.id;
            this.currentLegId = response.leg.leg.id;
            this.currentPlayerId = selectedPlayers[0];
            this.currentDartNumber = 1;
            
            console.log(`Game state updated:`);
            console.log(`  Match ID: ${this.currentMatchId}`);
            console.log(`  Leg ID: ${this.currentLegId}`);
            console.log(`  Player ID: ${this.currentPlayerId}`);
            console.log(`  Dart number: ${this.currentDartNumber}`);
            
            // Clear any offline throws from previous games
            this.offlineThrows = [];
            this.updateOfflineCount();
            
            this.hideModal('new-game-modal');
            
            // Load the game state to verify everything works
            await this.loadGameState();
            
            this.showMessage('New game started!');
            
        } catch (error) {
            console.error('Failed to start new game:', error);
            this.showError('Failed to start new game: ' + error.message);
        }
    }
        async showStatsModal() {
        if (!this.players.length) {
            await this.loadPlayers();
        }
        
        const statsContainer = document.getElementById('stats-display');
        statsContainer.innerHTML = '';
        
        // For now, show stats for first player
        if (this.players.length > 0) {
            try {
                const response = await this.apiRequest(`/api/stats/player/${this.players[0].id}`);
                const stats = response.stats;
                
                const statsHTML = `
                    <div class="stat-item">
                        <span class="stat-label">3-Dart Average:</span>
                        <span class="stat-value">${stats.three_dart_average}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Checkout %:</span>
                        <span class="stat-value">${stats.checkout_percentage}%</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Double Hit %:</span>
                        <span class="stat-value">${stats.double_hit_percentage}%</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Highest Finish:</span>
                        <span class="stat-value">${stats.highest_finish}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Highest Visit:</span>
                        <span class="stat-value">${stats.highest_scoring_visit}</span>
                    </div>
                `;
                
                statsContainer.innerHTML = statsHTML;
            } catch (error) {
                console.error('Failed to load stats:', error);
                statsContainer.innerHTML = '<p>Failed to load statistics.</p>';
            }
        }
        
        this.showModal('stats-modal');
    }
        showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'flex';
        }
    }
    
    hideModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
        }
    }
    
        updateButtonStates() {
        const throwButtons = document.querySelectorAll('.segment-btn, .special-btn');
        const nextPlayerBtn = document.getElementById('next-player-btn');
        
        // Determine if turn is complete
        const turnComplete = this.currentDartNumber > 3 || this.currentTurnIsBust;
        
        console.log(`updateButtonStates: dart=${this.currentDartNumber}, bust=${this.currentTurnIsBust}, turnComplete=${turnComplete}`);
        
        // Enable/disable throw buttons
        throwButtons.forEach(btn => {
            if (turnComplete) {
                btn.disabled = true;
                btn.style.opacity = '0.5';
                btn.style.cursor = 'not-allowed';
            } else {
                btn.disabled = false;
                btn.style.opacity = '1';
                btn.style.cursor = 'pointer';
            }
        });
        
        // Update next player button
        if (nextPlayerBtn) {
            if (turnComplete) {
                // Turn complete - enable next player button
                nextPlayerBtn.disabled = false;
                nextPlayerBtn.style.backgroundColor = this.currentTurnIsBust ? '#e94560' : '#4ecca3';
                nextPlayerBtn.textContent = this.currentTurnIsBust ? 'Next Player (Bust!)' : 'Next Player (Ready)';
            } else {
                // Mid-turn - disable next player button
                nextPlayerBtn.disabled = true;
                nextPlayerBtn.style.backgroundColor = '#666';
                nextPlayerBtn.textContent = 'Next Player';
            }
        }
    }
    
    resetGameState() {
        console.log('Resetting game state');
        this.currentMatchId = null;
        this.currentLegId = null;
        this.currentPlayerId = null;
        this.currentDartNumber = 1;
        this.offlineThrows = [];
        this.updateOfflineCount();
        
        // Clear the display
        document.getElementById('remaining-score').textContent = '501';
        document.getElementById('current-player').textContent = 'Player 1';
        
        const dartThrows = document.getElementById('dart-throws');
        if (dartThrows) {
            for (let i = 0; i < 3; i++) {
                dartThrows.children[i].textContent = `${i + 1}: `;
            }
        }
        
        document.getElementById('turn-total').textContent = 'Turn: 0';
        
        const scoresContainer = document.getElementById('player-scores');
        if (scoresContainer) {
            scoresContainer.innerHTML = '';
        }
    }
    
    forceRefreshGame() {
        console.log('Force refreshing game...');
        
        // Reset all state
        this.currentMatchId = null;
        this.currentLegId = null;
        this.currentPlayerId = null;
        this.currentDartNumber = 1;
        
        // Clear display
        this.resetGameState();
        
        // Find and load latest match
        this.findAndUseLatestMatch();
        
        this.showMessage('Game refreshed');
    }
        async checkConnection() {
        try {
            // Try to make a simple request to check connection
            await fetch('/api/players', { method: 'HEAD' });
            
            if (!this.isOnline) {
                this.isOnline = true;
                this.updateConnectionStatus();
                this.showMessage('Connection restored!');
                
                // Try to sync offline throws
                if (this.offlineThrows.length > 0) {
                    this.syncOfflineThrows();
                }
            }
        } catch (error) {
            if (this.isOnline) {
                this.isOnline = false;
                this.updateConnectionStatus();
                this.showMessage('Connection lost. Working offline...');
            }
        }
    }
    
    updateConnectionStatus() {
        const statusElement = document.getElementById('connection-status');
        const indicator = statusElement.querySelector('.status-indicator');
        const text = statusElement.querySelector('span:last-child');
        
        if (this.isOnline) {
            indicator.className = 'status-indicator online';
            text.textContent = 'Online';
        } else {
            indicator.className = 'status-indicator offline';
            text.textContent = 'Offline';
        }
    }
    
    updateOfflineCount() {
        const countElement = document.getElementById('offline-count');
        countElement.textContent = this.offlineThrows.length;
        
        // Show/hide offline queue indicator
        const queueElement = document.getElementById('offline-queue');
        if (this.offlineThrows.length > 0) {
            queueElement.style.display = 'block';
        } else {
            queueElement.style.display = 'none';
        }
    }
    
    async syncOfflineThrows() {
        if (!this.isOnline || this.offlineThrows.length === 0) return;
        
        const throwsToSync = [...this.offlineThrows];
        
        for (const throwData of throwsToSync) {
            try {
                await this.apiRequest(
                    `/api/matches/${this.currentMatchId}/legs/${this.currentLegId}/throw`,
                    'POST',
                    {
                        player_id: throwData.player_id,
                        segment: throwData.segment,
                        multiplier: throwData.multiplier,
                        dart_number: throwData.dart_number
                    }
                );
                
                // Remove from offline queue
                const index = this.offlineThrows.findIndex(t => t.timestamp === throwData.timestamp);
                if (index > -1) {
                    this.offlineThrows.splice(index, 1);
                }
            } catch (error) {
                console.error('Failed to sync throw:', error);
                break; // Stop trying if we get an error
            }
        }
        
        this.updateOfflineCount();
        
        if (this.offlineThrows.length === 0) {
            this.showMessage('All offline throws synced successfully!');
        }
    }
        async apiRequest(endpoint, method = 'GET', data = null) {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
        };
        
        if (data && (method === 'POST' || method === 'PUT')) {
            options.body = JSON.stringify(data);
        }
        
        console.log(`API Request: ${method} ${endpoint}`, data);
        
        const response = await fetch(endpoint, options);
        
        if (!response.ok) {
            let errorMessage = `API request failed: ${response.status} ${response.statusText}`;
            
            try {
                const errorData = await response.json();
                if (errorData.error) {
                    errorMessage = errorData.error;
                }
            } catch (e) {
                // Could not parse JSON error response
            }
            
            throw new Error(errorMessage);
        }
        
        return await response.json();
    }
    
    showMessage(message) {
        // Create a temporary message display
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message';
        messageDiv.textContent = message;
        messageDiv.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: #4ecca3;
            color: white;
            padding: 15px 30px;
            border-radius: 10px;
            z-index: 1001;
            font-weight: bold;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        `;
        
        document.body.appendChild(messageDiv);
        
        // Remove after 3 seconds
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.parentNode.removeChild(messageDiv);
            }
        }, 3000);
    }
    
    showError(error) {
        // Create a temporary error display
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error';
        errorDiv.textContent = error;
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: #e94560;
            color: white;
            padding: 15px 30px;
            border-radius: 10px;
            z-index: 1001;
            font-weight: bold;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        `;
        
        document.body.appendChild(errorDiv);
        
        // Remove after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 5000);
    }
    }

// Initialize the game when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.dartsGame = new DartsGame();
});

// Add scroll handling
function ensureVisible(element) {
    if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

// Make sure New Game button is visible on load
document.addEventListener('DOMContentLoaded', function() {
    // Check if we need to scroll to show controls
    const controls = document.querySelector('.game-controls');
    if (controls) {
        const viewportHeight = window.innerHeight;
        const controlsBottom = controls.getBoundingClientRect().bottom;
        
        if (controlsBottom > viewportHeight - 50) {
            // Scroll to show controls
            controls.scrollIntoView({ behavior: 'smooth', block: 'end' });
        }
    }
    
    // Add scroll to buttons
    const newGameBtn = document.getElementById('new-game-btn');
    if (newGameBtn) {
        newGameBtn.addEventListener('click', function() {
            setTimeout(() => {
                const modal = document.getElementById('new-game-modal');
                if (modal) {
                    modal.scrollTop = 0;
                }
            }, 100);
        });
    }
});

// Reset game state on page load
window.addEventListener('load', function() {
    // Clear any stored game state
    localStorage.removeItem('dartsGameState');
    
    // Reset the game object
    if (window.dartsGame) {
        window.dartsGame.currentMatchId = null;
        window.dartsGame.currentLegId = null;
        window.dartsGame.currentPlayerId = null;
        window.dartsGame.currentDartNumber = 1;
        window.dartsGame.offlineThrows = [];
    }
});

// Add CSS for messages
const style = document.createElement('style');
style.textContent = `
    .message, .error {
        animation: slideIn 0.3s ease-out;
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateX(-50%) translateY(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(-50%) translateY(0);
        }
    }
    
    @keyframes slideOut {
        from {
            opacity: 1;
            transform: translateX(-50%) translateY(0);
        }
        to {
            opacity: 0;
            transform: translateX(-50%) translateY(-20px);
        }
    }
`;
document.head.appendChild(style);
