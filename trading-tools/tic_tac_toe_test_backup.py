def print_board(board: list[str]) -> None:
    """
    Print the current state of the tic-tac-toe board.
    
    Args:
        board: A list of 9 strings representing the board positions
    """
    print("\n")
    for i in range(0, 9, 3):
        print(f" {board[i]} | {board[i+1]} | {board[i+2]} ")
        if i < 6:
            print("-----------")
    print("\n")


def check_winner(board: list[str]) -> str | None:
    """
    Check if there is a winner in the current board state.
    
    Args:
        board: A list of 9 strings representing the board positions
        
    Returns:
        The winning player ('X' or 'O') if there is a winner, None otherwise
    """
    # Define all possible winning combinations
    winning_combinations = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
        [0, 4, 8], [2, 4, 6]              # Diagonals
    ]
    
    for combo in winning_combinations:
        if board[combo[0]] == board[combo[1]] == board[combo[2]] != " ":
            return board[combo[0]]
    
    return None


def is_board_full(board: list[str]) -> bool:
    """
    Check if the board is full (no empty spaces).
    
    Args:
        board: A list of 9 strings representing the board positions
        
    Returns:
        True if the board is full, False otherwise
    """
    return " " not in board


def get_valid_move(board: list[str]) -> int:
    """
    Get a valid move from the player.
    
    Args:
        board: A list of 9 strings representing the board positions
        
    Returns:
        An integer representing the position (1-9) where the player wants to place their mark
    """
    while True:
        try:
            move = input("Enter your move (1-9): ")
            move_int = int(move)
            
            if move_int < 1 or move_int > 9:
                print("Please enter a number between 1 and 9.")
                continue
                
            if board[move_int - 1] != " ":
                print("That position is already taken. Choose another.")
                continue
                
            return move_int
            
        except ValueError:
            print("Please enter a valid number.")


def play_game() -> None:
    """
    Play a single game of tic-tac-toe.
    """
    # Initialize the board
    board = [" "] * 9
    current_player = "X"
    
    print("Welcome to Tic-Tac-Toe!")
    print("Positions are numbered as follows:")
    print_board(["1", "2", "3", "4", "5", "6", "7", "8", "9"])
    
    while True:
        print_board(board)
        print(f"Player {current_player}'s turn")
        
        # Get player move
        move = get_valid_move(board)
        
        # Update board
        board[move - 1] = current_player
        
        # Check for winner
        winner = check_winner(board)
        if winner:
            print_board(board)
            print(f"Player {winner} wins!")
            break
            
        # Check for draw
        if is_board_full(board):
            print_board(board)
            print("It's a draw!")
            break
            
        # Switch player
        current_player = "O" if current_player == "X" else "X"


def main() -> None:
    """
    Main function to run the tic-tac-toe game with replay option.
    """
    while True:
        play_game()
        
        # Ask if player wants to replay
        while True:
            play_again = input("Do you want to play again? (y/n): ").lower()
            if play_again in ['y', 'yes']:
                break
            elif play_again in ['n', 'no']:
                print("Thanks for playing!")
                return
            else:
                print("Please enter 'y' for yes or 'n' for no.")


if __name__ == "__main__":
    main()