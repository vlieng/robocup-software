import robocup
import constants
import single_robot_composite_behavior
import enum
import behavior
import main
import skills.move
import subprocess
import random

## Motivates, encourages, and directs the team.
class Coach(single_robot_composite_behavior.SingleRobotCompositeBehavior):

    MaxSpinAngle = 360
    SpinPerTick = 1

    OurScore = 0
    TheirScore = 0

    class State(enum.Enum):
        watching = 0
        celebrating = 1
        motivating = 2
        strategizing = 3

    def __init__(self):
        super().__init__(continuous=True, autorestart = lambda: False)#self.State != self.State.strategizing)
        self.spin_angle = 0

        for state in Coach.State:
            self.add_state(state, behavior.Behavior.State.running)

        self.add_transition(behavior.Behavior.State.start, self.State.watching,
                            lambda: True, 'immediately')

        # Transitions into and out of celebration
        self.add_transition(self.State.watching, self.State.celebrating,
                            lambda: self.our_score_increased(), 'goal scored')
        self.add_transition(self.State.celebrating, self.State.watching,
                            lambda: self.spin_angle > Coach.MaxSpinAngle, 'done with celebration')

        self.add_transition(self.State.watching, self.State.motivating,
                            lambda: self.their_score_increased(), 'Let a goal through')
        self.add_transition(self.State.motivating, self.State.watching,
                            lambda: True, 'done talking')

        self.add_transition(self.State.watching, self.State.strategizing,
                            lambda: main.game_state().is_stopped(), 'Timeout')
        self.add_transition(self.State.strategizing, self.State.watching,
                            lambda: not main.game_state().is_stopped(), 'Timeout over')

    def our_score_increased(self):
        if (Coach.OurScore < main.game_state().our_score):
            return True
        else:
            Coach.OurScore = main.game_state().our_score
            return False
    def their_score_increased(self):
        if (Coach.TheirScore < main.game_state().their_score):
            return True
        else:
            Coach.TheirScore = main.game_state().their_score
            return False

    def on_enter_running(self):
        move_point = robocup.Point(-constants.Field.Width / 2 - constants.Robot.Radius * 2,
                                   constants.Field.Length / 3)

        move = skills.move.Move(move_point)
        self.add_subbehavior(move, 'coach')

    def on_exit_running(self):
        self.remove_all_subbehaviors()

    def execute_watching(self):
        move = self.subbehavior_with_name('coach')

        # Face ball
        if (main.ball().valid and move.robot is not None):
            move.robot.face(main.ball().pos)

            # Don't cross to the opponent's side of the field
            max_y = constants.Field.Length / 2 - constants.Robot.Radius * 2
            min_y = constants.Robot.Radius * 2
            move_y_pos = max(min(main.ball().pos.y, max_y), min_y)

            move.pos = robocup.Point(move.pos.x, move_y_pos)

    def on_enter_celebrating(self):
        Coach.OurScore = main.game_state().our_score

    def execute_celebrating(self):
        move = self.subbehavior_with_name('coach')
        # Face ball
        if (move.robot is not None):
            angle = move.robot.angle
            facing_point = robocup.Point.direction(angle) + move.robot.pos
            facing_point.rotate(move.robot.pos, Coach.SpinPerTick)
            self.spin_angle += Coach.SpinPerTick
            move.robot.face(facing_point)

    def on_enter_motivating(self):
        Coach.TheirScore = main.game_state().their_score

        print("\n\nListen up:")
        print(Coach.fortune_wrapper())

    def on_enter_strategizing(self):
        #pick a robot to talk to
        target_bot = random.randint(0, ((len(main.our_robots()) - 1) if (main.our_robots() is not None) else 0));
        self.subbehavior_with_name('coach').pos = main.our_robots()[target_bot].pos
        print("\n\n Alright Number " + str(target_bot) + " here is the plan:");

    def execute_strategizing(self):
        #Stops coach from talking too much
        max_responses = 5000
        current_plan = random.randint(0, max_responses)
        
        #because python is too cool for switch statements
        if (current_plan == max_responses):
            print("\n*incoherent mumbling*")
        elif (current_plan == max_responses - 1):
            print("\nThey'll never see it coming!")
        elif (current_plan == max_responses - 2):
            print("\n*wild robot appendage gestures*")
        elif (current_plan == max_responses - 3):
            print("\nAnd that's when we pull out the soldering irons")
        elif (current_plan == max_responses - 4):
            print("\n*coach violently hawks a loogie*")
        elif (current_plan == max_responses - 5):
            print("\nSweep the Leg")
        elif (current_plan == max_responses - 6):
            print("\nIs it necesarry for me to drink my own urine? No, but I do it anyway because its sterile and I like the taste")
        elif (current_plan == max_responses - 7):
            print("\nThere's nothing in the rules about golf clubs")
        elif (current_plan == max_responses - 8):
            print("\n*coach points violently at the ref*")
        elif (current_plan == max_responses - 9):
            print("\n*coach slyly passes the player a pill*")
        elif (current_plan == max_responses - 10):
            print("\nYes, the soup last night was delicious")

    def on_exit_strategizing(self):
        print("\n*coach gives the player an invigorating butt slap*\nGo get'em")

    @staticmethod
    ## Returns a fortune.
    def fortune_wrapper():
        try:
            # Prefer -o if available
            fortune = subprocess.check_output(["fortune", "-o"])
            fortune = fortune.decode("utf-8")
        except subprocess.CalledProcessError:
            try:
                # Fall back to any fortune
                fortune = subprocess.check_output(["fortune"])
                fortune = fortune.decode("utf-8")
            except subprocess.CalledProcessError:
                # We must be on Windows, give a sna... enlightening remark. (install fortune!)
                fortune = '''"There is no such thing as a typical user, and if there were, it wouldn't be you" - #usability'''
        return fortune

    def role_requirements(self):
        reqs = super().role_requirements()
        reqs.robot_change_cost = 20.0
        return reqs

