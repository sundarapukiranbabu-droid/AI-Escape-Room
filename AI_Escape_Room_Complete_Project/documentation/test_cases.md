# AI Escape Room – Version 2 Test Cases

These test cases record the functional checks shown in the supplied Version 2 screenshots. The results are specific to the test runs performed and do not establish protection against every possible adversarial input.

| Test ID | Scenario | Test input / action | Expected result | Observed result | Status |
|---|---|---|---|---|---|
| TC01 | Successful escape | Solve the bookshelf (1234), discover the key behind the painting, open the drawer, solve the desk puzzle (2468), and complete the exit challenge. | The game accepts valid actions in sequence and displays an escape-success message with progress 5/5. | Escape-success screen displayed; progress 5/5 and final score 825. | PASSED |
| TC02 | Incorrect bookshelf answer | Enter `1111` for the bookshelf sequence. | The answer is rejected, the stage does not advance, and the game gives feedback. | The game reported that the sequence did not fit and deducted 10 points. | PASSED |
| TC03 | Inventory and locked drawer | Complete the bookshelf and painting steps, collect the brass key, and use it on the locked drawer. | The key is added to inventory; the drawer opens only after the key is obtained. | The brass key appeared in inventory and the drawer-open message was displayed. | PASSED |
| TC04 | Incorrect desk code | After opening the drawer, enter `2345` as the desk code. | The code is rejected, the desk puzzle remains unsolved, and feedback is shown. | The game reported an incorrect code and deducted 10 points. | PASSED |
| TC05 | Restart functionality | Click Restart Game after gameplay has begun. | Puzzle progress returns to 0/5, inventory is cleared, objects return to their initial locked state, and the selected difficulty's starting values are restored. | Hard difficulty screenshot showed 200 score, 2 hints, 0/5 progress, empty inventory, and locked room objects. | PASSED |

## Evaluation

The screenshots demonstrate successful completion, rejection of incorrect answers, inventory-based drawer access, and reset behaviour. These checks show how Version 2 uses Python-managed progress and validation for the tested game actions. Version 1's conversational design does not provide the same strict Python-controlled validation demonstrated in Version 2.

## Evidence files

- `../screenshots/test_1_successful_escape.png`
- `../screenshots/test_2_incorrect_bookshelf.png`
- `../screenshots/test_3_inventory_and_desk_code.png`
- `../screenshots/test_4_incorrect_desk_code.png`
- `../screenshots/test_5_restart_hard.png`
