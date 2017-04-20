from scale import Scale


def main():
    print "Running..."
    scale = Scale()

    # call scale.lock_previous_weight when motion is detected to stop updating the stable weight value
    # call scale.is_weight_reduced when motion is no longer detected to see if the stable weight has decreased
    # call scale.lock_previous_weight when motion is no longer detected to start updating the stable weight value again

    while True:

        # ...rest of your program's logic...

        # Allow breaking out of the loop
        choice = input("Enter Q to quit, or press return to continue")
        if choice.lower() == "q":
            scale.stop()
            break

    # scale.is_weight_reduced()


    # scale.stop()

main()
