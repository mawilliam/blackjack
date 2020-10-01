'''
Description: used to test student's solution's to the Blackjack final project
Imports their script and uses the player_action and wager functions
Calculates their win percentage & earnings over many simulations
'''
import random
import blackjack


class Hand:
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

    def __init__(self):
        self.cards = []
        self.wager = 1

    def calc_hand_value(self):
        '''
        returns the blackjack hand value and type
        if the hand contains an Ace used as an 11, then it is soft;
        otherwise, it is hard
        '''
        value = 0
        type = 'H'
        ace = False

        for card in self.cards:
            value += self.card_values[card]

            if card == 'A':
                ace = True

        if ace and value <= 11:
            value += 10
            type = 'S'

        return (value, type)

    def is_valid(self, action):
        if action == 'split':
            if self.cards[0] == self.cards[1] and len(self.cards) == 2:
                return True
            else:
                SPLIT = True
                return False
        else:
            if len(self.cards) == 2:
                return True
            else:
                DOUBLE = True
                return False

    def dealer_turn(self, shoe):
        '''
        implements the pre-defined rules of the dealer

        Parameters
        ----------
        shoe -- a list containing the cards remaining in the current shoe

        Returns
        -------
        list containing the cards in the dealer's final hand
        '''
        # Dealer turn: hit until H17, then stay
        while self.calc_hand_value()[0] < 17 or \
                self.calc_hand_value() == (17, 'S'):
            self.cards.append(shoe.deal_card())


class Player:
    def __init__(self):
        self.hands = [Hand()]

    def split_cards(self, hand_index, shoe):
        # create a new hand, move the card into it, and set the wager
        self.hands.append(Hand())
        self.hands[-1].cards.append(self.hands[hand_index].cards.pop())
        self.hands[-1].wager = self.hands[hand_index].wager

        # add a card to each hand
        self.hands[hand_index].cards.append(shoe.deal_card())
        self.hands[-1].cards.append(shoe.deal_card())

    def player_turn(self, hand_index, dealer_card, shoe):
        # base case: last element and action != split
        action = blackjack.player_action(self.hands[hand_index].cards[:],
                                         dealer_card,
                                         shoe.played_cards[:])

        if action == 'split':
            # split
            if self.hands[hand_index].is_valid('split'):
                self.split_cards(hand_index, shoe)
                self.player_turn(hand_index, dealer_card, shoe)
            else:
                # invalid: stand
                action = 'stand'

        if action == 'double':
            if self.hands[hand_index].is_valid('double'):
                self.hands[hand_index].wager *= 2
                self.hands[hand_index].cards.append(shoe.deal_card())
            else:
                # invalid: hit
                action = 'hit'

        while action == 'hit':
            self.hands[hand_index].cards.append(shoe.deal_card())

            if self.hands[hand_index].calc_hand_value()[0] >= 21:
                break

            action = blackjack.player_action(self.hands[hand_index].cards[:],
                                             dealer_card,
                                             shoe.played_cards[:])

        hand_index += 1
        if hand_index < len(self.hands):
            self.player_turn(hand_index, dealer_card, shoe)


class Shoe:
    deck = [2, 3, 4, 5, 6, 7, 8, 9, 10, 'J', 'Q', 'K', 'A'] * 4

    def __init__(self, num_decks):
        self.cards = self.deck * num_decks
        self.played_cards = []

    def shuffle(self):
        random.shuffle(self.cards)

    def deal_card(self):
        card = self.cards.pop()
        self.played_cards.append(card)
        return card


class Stats:
    def __init__(self):
        self.outcomes = []
        self.chips = []
        self.total_rounds = 0

    def record_result(self, result, wager):
        self.outcomes.append(result)
        self.chips.append(wager)

    def calc_stats(self):
        wins = 0
        ties = 0
        for result in self.outcomes:
            if result == 'W':
                wins += 1
            elif result == 'T':
                ties += 1

        win_pct = wins / len(self.outcomes)
        avg_winnings = sum(self.chips) / len(self.chips)
        tie_pct = ties / len(self.outcomes)
        return (win_pct, avg_winnings, tie_pct)


def simulate(num_sims, num_decks):
    '''
    simulates playing many hands of blackjack using a shoe of 8 decks

    keeps track of the player winning percentage and earnings
    '''
    # Stats
    stats = Stats()

    SPLIT = False
    DOUBLE = False
    BET = False

    for run in range(num_sims):

        # Simulating a shoe of Blackjack
        shoe = Shoe(num_decks)
        shoe.shuffle()

        # Stopping criteria
        cut = random.uniform(len(shoe.cards) / 4, len(shoe.cards) / 3)

        while len(shoe.cards) > cut:
            stats.total_rounds += 1
            player = Player()  # player could split hand into multiple hands
            dealer = Hand()

            # Get wager
            try:
                player.hands[0].wager = blackjack.wager(shoe.played_cards[:])

                # Check if it is valid
                if player.hands[0].wager < 1:
                    player.hands[0].wager = 1
                    BET = True
                elif player.hands[0].wager > 100:
                    player.hands[0].wager = 100
                    BET = True

            except AttributeError:
                BET = True
                player.hands[0].wager = 1

            # Deal
            for i in range(4):
                if i % 2 == 0:
                    # player card
                    player.hands[0].cards.append(shoe.deal_card())
                else:
                    # dealer card
                    dealer.cards.append(shoe.deal_card())

            # Check for blackjack
            player_value = player.hands[0].calc_hand_value()[0]
            dealer_value = dealer.calc_hand_value()[0]

            if player_value == 21 and dealer_value == 21:
                # tie
                stats.record_result('T', 0)
                continue

            elif player_value == 21:
                # player win
                stats.record_result('W', player.hands[0].wager * 1.5)
                continue

            elif dealer_value == 21:
                # dealer win
                stats.record_result('L', -player.hands[0].wager)
                continue

            # Player turn
            # Options: split, double, hit, stand
            player.player_turn(0, dealer.cards[0], shoe)

            # Check if dealer needs to go
            for hand in player.hands:
                if hand.calc_hand_value()[0] <= 21:
                    # Dealer turn
                    dealer.dealer_turn(shoe)
                    break

            # Tabulate results
            dealer_value = dealer.calc_hand_value()[0]
            for hand in player.hands:
                player_value = hand.calc_hand_value()[0]

                if player_value > 21:
                    # dealer wins
                    stats.record_result('L', -hand.wager)

                elif dealer_value > 21 or player_value > dealer_value:
                    # player wins
                    stats.record_result('W', hand.wager)

                elif dealer_value > player_value:
                    # dealer wins
                    stats.record_result('L', -hand.wager)

                else:
                    # tie
                    stats.record_result('T', 0)

    if BET:
        print('Your wager() function did not behave properly')

    if SPLIT:
        print('You tried to split when it was not allowed')

    if DOUBLE:
        print('You tried to double when it was not allowed')

    results = stats.calc_stats()
    # print('Win percentage: {:.3f}%'.format(results[0]*100))
    # print('Tie percentage: {:.3f}%'.format(results[2]*100))
    # print('Avg winnings per hand: {:.3f} units'.format(results[1]))
    # print('Total rounds: {}'.format(stats.total_rounds))

    print('{:.3f}'.format(results[0]))
    print('{:.3f}'.format(results[1]))
    print('{:.3f}'.format(results[2]))


if __name__ == "__main__":
    random.seed(7487)
    num_decks = 8
    num_sims = 1000
    simulate(num_sims, num_decks)
