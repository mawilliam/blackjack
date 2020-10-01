'''
Desription: Provides the minimum functionality necessary in order to properly
test the quality of this solution for the finally

Functions:
player_action(player_hand, dealer_card, hand_number)
wager()

'''
import random


card_values = {
    2: 2,
    3: 3,
    4: 4,
    5: 5,
    6: 6,
    7: 7,
    8: 8,
    9: 9,
    10: 10,
    'J': 10,
    'Q': 10,
    'K': 10,
    'A': 1
    }


def calc_hand_value(cards):
    '''
    returns the blackjack hand value and type
    if the hand contains an Ace used as an 11, then it is soft;
    otherwise, it is hard
    '''
    value = 0
    hand_type = 'H'
    ace = False

    for card in cards:
        value += card_values[card]

        if card == 'A':
            ace = True

    if ace and value <= 11:
        value += 10
        hand_type = 'S'

    return (value, hand_type)


def dealer_action(dealer_hand):
    hand_value = calc_hand_value(dealer_hand)

    if hand_value[0] < 17:
        return 'hit'
    elif hand_value[0] == 17 and hand_value[1] == 'S':
        return 'hit'
    else:
        return 'stand'


def simulate_dealer():
    dealer_transition = {}
    for card in card_values:
        dealer_transition[card_values[card]] = {}

        for end in [17, 18, 19, 20, 21, 'Bust']:
            dealer_transition[card_values[card]][end] = 0

    for sim in range(10000):
        shoe = [2, 3, 4, 5, 6, 7, 8, 9, 10, 'J', 'Q', 'K', 'A'] * 4 * 8
        random.shuffle(shoe)

        # Stopping criteria
        cut = random.uniform(len(shoe) / 4, len(shoe) / 3)

        while len(shoe) > cut:
            dealer_hand = [shoe.pop(), shoe.pop()]

            while dealer_action(dealer_hand) == 'hit':
                dealer_hand.append(shoe.pop())

            hand_value = calc_hand_value(dealer_hand)[0]

            if hand_value > 21:
                dealer_transition[card_values[dealer_hand[0]]]['Bust'] += 1
            else:
                dealer_transition[card_values[dealer_hand[0]]][hand_value] += 1

    for up in dealer_transition:
        total = sum([dealer_transition[up][end]
                     for end in dealer_transition[up]])

        for end in dealer_transition[up]:
            dealer_transition[up][end] /= total

    return dealer_transition


dealer_transition = simulate_dealer()


def random_player_action(player_hand):
    """randomly choose a valid action"""
    valid_actions = ['hit', 'stand']
    if len(player_hand) == 2 and player_hand[0] == player_hand[1]:
        valid_actions.append('split')
        valid_actions.append('double')
    elif len(player_hand) == 2:
        valid_actions.append('double')
        
    return random.choice(valid_actions)
    

def rl_turn(hands, hand_index, hand_actions, shoe):
    action = random_player_action(hands[hand_index])
    
    if action == 'split':
        # Add (state, action) to history & initialize new list
        hand_actions[hand_index].append(((calc_hand_value(hands[hand_index])[0],
                                          'D'),
                                         'split'))
        hand_actions.append([])
        
        hands.append([])  # add a new hand to the list of hands
        hands[-1].append([hands[hand_index].pop()])  # split cards btw two hands
        
        # Add a card to each hand
        hands[hand_index].append(shoe.pop())
        hands[-1].append(shoe.pop())
        
        # recursively call rl_turn with the same hand index
        hands, hand_actions, shoe = rl_turn(hands,
                                            hand_index,
                                            hand_actions,
                                            shoe)
        
    elif action == 'double':
        # Add (state, action) to history
        if hands[hand_index][0] == hands[hand_index][1]:
            hand_actions[hand_index].append(((calc_hand_value(hands[hand_index])[0],
                                              'D'),
                                             'double'))
        else:
            hand_actions[hand_index].append((calc_hand_value(hands[hand_index]),
                                             'double'))
        
        hands[hand_index].append(shoe.pop())  # deal card
        
    # continue to hit until 20
    while action == 'hit':
        # Add (state, action) to history
        hand_actions[hand_index].append((calc_hand_value(hands[hand_index]),
                                         'hit'))
                                         
        hands[hand_index].append(shoe.pop())  # deal card
        
        if calc_hand_value(hands[hand_index]) >= 21:
            break
            
        action = random_player_action(hands[hand_index])
    
    # Add (state, action) to history
    hand_actions[hand_index].append((calc_hand_value(hands[hand_index]),
                                     'stand'))

    hand_index += 1
    if hand_index < len(hands):
        # recursively call rl_turn with the new hand index
        hands, hand_actions, shoe = rl_turn(hands,
                                            hand_index,
                                            hand_actions,
                                            shoe)
                                            
    return hands, hand_actions, shoe

def reinforcement_learning():
    """
    simulates blackjack to populate lookup tables for the best policy given
    repeated sampling
    """
    # initialize a container to keep track of results
    states = {}
    iter_1 = [2*i for i in range(2, 11)] + [13]
    iter_2 = list(range(5, 21))
    iter_3 = list(range(13, 21))
    
    for hand_value, hand_type in zip(iter_1 + iter_2 + iter_3,
                                     ['P']*10 + ['H']*16 + ['S']*8):
        for up in [2, 3, 4, 5, 6, 7, 8, 9, 10, 'A']:
            states[(hand_value, hand_type, up)] = {}
            for action in ['split', 'double', 'hit', 'stand']:
                if hand_type == 'P' or action != 'split':
                    states[(hand_value, hand_type, up)][action] = []

    
    for sim in range(10000):
        shoe = [2, 3, 4, 5, 6, 7, 8, 9, 10, 'J', 'Q', 'K', 'A'] * 4 * 8
        random.shuffle(shoe)

        # Stopping criteria
        cut = random.uniform(len(shoe) / 4, len(shoe) / 3)

        while len(shoe) > cut:
            # deal
            player_hand = []  # list of lists to keep track of all player hands
            player_hand.append([])
            
            # list of lists to track (state, action) history for each hand
            player_actions = []
            player_actions.append([])
            
            dealer_hand = []
            for i in range(2):
                player_hand[0].append(shoe.pop())
                dealer_hand.append(shoe.pop())
                
            # check for blackjack
            player_value = calc_hand_value(player_hand)
            dealer_value = calc_hand_value(dealer_hand)
            
            if player_value[0] == 21 or dealer_value[0] == 21:
                continue

            dealer_up = dealer_hand[0]
            player_hand, player_actions, shoe = rl_turn(player_hand,
                                                        0,
                                                        player_actions,
                                                        shoe)
                                                        
            # check if the dealer needs to go
            for hand in player_hand:
                if calc_hand_value(hand)[0] <= 21:
                    while dealer_action(dealer_hand) == 'hit':
                        dealer_hand.append(shoe.pop())
                    break

            dealer_value = calc_hand_value(dealer_hand)[0]

            # tabulate results
            for hand_index, hand in enumerate(player_hand):
                wager = 1
                if player_actions[hand_index][1] == 'double':
                    wager = 2
                
                player_value = calc_hand_value(hand)[0]
                if player_value > 21:
                    # dealer wins
                    outcome = -wager
                elif dealer_value > 21 or player_value > dealer_value:
                    # player wins
                    outcome = wager
                elif dealer_value > player_value:
                    # dealer wins
                    outcome = -wager
                else:
                    # tie
                    outcome = 0
                    
                # record result for each state in the hand's history
                for state, action in player_actions[hand_index]:
                    states[(state[0], state[1], dealer_up)] \
                        [action].append(outcome)
                        
    return states


states = reinforcement_learning()


def find_optimal_action(player_hand, dealer_up, states=states):
    """convert results into optimal values for each state"""
    hand_value = calc_hand_value(player_hand)
    first = False
    state = (hand_value[0], hand_value[1], dealer_up)
    if len(player_hand) == 2 and player_hand[0] == player_hand[1]:
        state = (hand_value[0], 'D', dealer_up)
        first = True
    elif len(player_hand) == 2:
        first = True

    best = -100000
    best_action = ''
    for action, results in states[state].items():
        if not first and action == 'double':
            continue
        exp_val = sum(results) / len(results)
        if exp_val > best:
            best = exp_val
            best_action = action
    
    return best_action


def simple_strategy(player_hand, dealer_card):
    '''
    implements the simple strategy: https://www.youtube.com/watch?v=2bRxpVx677k

    Parameters
    ----------
        - player_hand: list of cards in the players hand_number
        - dealer_card: dealer's up card (string)

    Returns
    -------
        - action: either 'hit', 'stand', 'split', or 'double'
    '''
    hand_value = calc_hand_value(player_hand)

    if player_hand == ['A', 'A'] or player_hand == [8, 8]:
        # always split aces or 8s
        return 'split'
    elif hand_value[0] == 11:
        # always double on 11
        return 'double'
    elif hand_value[0] < 18 and hand_value[1] == 'S':
        # always hit on soft 17 or less
        return 'hit'
    elif hand_value[1] == 'S':
        # always stand on soft 18 or more
        return 'stand'
    elif dealer_card in [2, 3, 4, 5, 6]:
        # hard hand and dealer has a low card
        if 9 <= hand_value[0] <= 10 and len(player_hand) == 2:
            return 'double'
        elif hand_value[0] < 12:
            # always hit less than 12
            return 'hit'
        else:
            return 'stand'
    else:
        # hard hand and dealer has high card
        # mimic dealer
        if hand_value[0] < 17:
            return 'hit'
        else:
            return 'stand'


def bust_odds(player_hand, played_cards):
    hand_value = calc_hand_value(player_hand)

    if hand_value[1] == 'S' or hand_value[0] < 12:
        return 0

    odds = 0
    for card in card_values:
        if hand_value[0] + card_values[card] > 21:
            odds += (32 - played_cards.count(card)) \
                / ((52 * 8) - len(played_cards))

    return odds


def get_count(played_cards):
    count = 0
    count += sum([played_cards.count(i) for i in [2, 3, 4, 5, 6]])
    count -= sum([played_cards.count(i) for i in [10, 'J', 'Q', 'K', 'A']])

    count /= ((52 * 8) - len(played_cards)) // 52

    return count


def calc_expected_return(player_value, player_odds, dealer_odds, wager):
    """
    calculates and returns the expected return for a player's hand value
    over all possible dealer outcomes
    E[return | player hand, dealer up card, wager] =
        sum of (wager * odds of action outcome * odds of dealer result)
        for all possible action outcomes (cards), dealer results (17 - Bust)

    Note 1: losing is negative profit, tying is 0, positive return means more
    likely to win than lose, negative is more likely to lose than win

    Parameters
    ----------
    player_value: int, final hand value
    player_odds: float, probability of player getting to the current end state
    dealer_odds: dict, dealer's transition probability matrix for their up card
    wager: int, unit wager (1 or 2 depending on the player action)

    Returns
    -------
    float, representing the expected value
    """
    exp_value = 0

    # Check if player busted
    if player_value > 21:
        return -wager * player_odds

    # iterate over all possible dealer outcomes and sum expected return
    for end, odds in dealer_odds.items():
        if end == 'Bust':
            exp_value += wager * player_odds * odds
        elif end < player_value:
            exp_value += wager * player_odds * odds
        elif end > player_value:
            exp_value -= wager * player_odds * odds

    return exp_value


def expand_tree(player, card_odds, dealer_odds, action):
    """
    calculates and returns the expected return for a unit wager
    E[return | player hand, dealer up card, player action] =
        sum of (wager * odds of action outcome * odds of dealer result)
        for all possible action outcomes (cards), dealer results (17 - Bust)

    Note 1: losing is negative profit, tying is 0, positive return means more
    likely to win than lose, negative is more likely to lose than win

    Parameters
    ----------
    player: list, players cards in current hand
    card_odds: dict, probability each card is next in shoe given played cards
    dealer_odds: dict, dealer's transition probability matrix given up card
    action: string, action (hit, split, double) to calculate

    Returns
    -------
    float, representing the expected value
    """
    exp_value = 0
    wager = 1
    final = False

    if action == 'split':
        new = [player[0]]
        wager = 2
    elif action == 'double':
        new = player[:]
        wager = 2
        final = True
    else:
        new = player[:]

    # iterate over all possible card outcomes
    for card in [2, 3, 4, 5, 6, 7, 8, 9, 10, 'J', 'Q', 'K', 'A']:
        # update the hand value for the card outcome
        hand_value = calc_hand_value(new + [card])[0]

        # calculate the expected return
        # recursively call find best action for hands less than threshold
        if hand_value > 21:
            exp_value -= wager * card_odds[card]
        elif hand_value < 18 and not final:
            # call find best action recursively
            exp_value += wager * card_odds[card] \
                * find_best_action(new + [card],
                                   card_odds,
                                   dealer_odds)[1]
        else:
            exp_value += calc_expected_return(hand_value,
                                              card_odds[card],
                                              dealer_odds,
                                              wager)

    return exp_value


def find_best_action(player, card_odds, dealer_odds, split=False):
    """
    returns optimal action based on expected return given current state

    Note 1: only expanding tree for split once so there isn't an infinite loop

    Parameters
    ----------
    player: list, players cards in current hand
    card_odds: dict, odds of getting each card based on the played cards
    dealer_odds: dict, dealer's transition probability matrix for up card

    Returns
    -------
    tuple, representing the (optimal action, expected return)
    """
    possible_actions = ['hit', 'stand']
    exp_return = {}

    if len(player) == 2 and player[0] == player[1] and split:
        possible_actions.append('split')
        possible_actions.append('double')
    elif len(player) == 2:
        possible_actions.append('double')

    best = 'hit'

    for action in possible_actions:
        if action == 'stand':
            hand_value = calc_hand_value(player)[0]
            exp_return[action] = calc_expected_return(hand_value, 1,
                                                      dealer_odds, 1)
        else:
            exp_return[action] = expand_tree(player[:],
                                             card_odds,
                                             dealer_odds,
                                             action)
        if exp_return[action] > exp_return[best]:
            best = action

    return (best, exp_return[best])


def informed_strategy(player_hand, played_cards, dealer_odds):
    """
    determines the best action based on the expected return of all possible
    actions

    Note 1: optimal action known if double not an option & hand value < 12: hit

    Parameters
    ----------
    player_hand: list, players cards in current hand
    played_cards: list, all cards played thus far
    dealer_odds: dict, dealer's transition probability matrix given up card

    Returns
    -------
    action: string, action (hit, stand, split, double) to calculate
    """
    if len(player_hand) != 2 and calc_hand_value(player_hand)[0] < 12:
        return 'hit'

    card_odds = {}
    for card in [2, 3, 4, 5, 6, 7, 8, 9, 10, 'J', 'Q', 'K', 'A']:
        card_odds[card] = (32 - played_cards.count(card)) \
            / ((52*8) - len(played_cards))

    return find_best_action(player_hand[:],
                            card_odds,
                            dealer_odds,
                            split=True)[0]


def player_action(player_hand, dealer_card, played_cards,
                  dealer_odds=dealer_transition):
    '''
    determines the most appropriate action based on the current state of the
    game

    Parameters
    ----------
    player_hand: list of cards in the players hand_number
    dealer_card: dealer's up card (string)
    played_cards: list of cards played so far

    Returns
    -------
    string: either 'hit', 'stand', 'split', or 'double'
    '''
    strategy = 'reinforcement'

    if strategy == 'player':
        return simple_strategy(player_hand, dealer_card)
    elif strategy == 'informed':
        return informed_strategy(player_hand[:],
                                 played_cards[:],
                                 dealer_transition[card_values[dealer_card]])
    elif strategy == 'reinforcement':
        return find_optimal_action(player_hand, dealer_card)
    else:
        return 'stand'


def wager(played_cards):
    '''
    bet for the hand (1 - 100)
    '''
    # return 1
    count = get_count(played_cards[:])

    # positive count means there are more high cards left in the deck
    # negative count means there are more low cards left in the deck
    if count <= 0:
        return 1
    else:
        return min(100, count * 10)
