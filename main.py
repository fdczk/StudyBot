from discord.ext import commands
import os
import discord

bot = commands.Bot(command_prefix='!', help_command=None)
password = os.environ['password']

userToList = dict()
# will map user's name to a List (of Task objects)
# if there were multiple lists, it would map user to a set of List objects

# userToCompleted = dict() might be implemented in the future
# will map each user to a List of Tasks marked completed (but only the 10 most recent)

currentUser = ""
# temporarily holds the last user's discord handle


def getProgress(task):  ## purely for sorting purposes
    return task.progress


class List:
    # name = "" # if I end up expanding to allow users to have multiple
    isLocked = True
    tasks = []  # stores all task objects in a list

    def __init__(self):
        self.locked = False

    def addTask(self, taskName):
        task = Task(taskName)
        self.tasks.append(task)

    def dropTask(self, index):
        if (index == 0 or len(self.tasks) == index + 1):
            print(
                "Oop, try again. The number received didn't match any task in your list"
            )
        else:
            taskDropped = self.tasks.pop(index - 1).name
            print("*" + taskDropped + "* successfully removed")

    def sortByProgress(self):
        self.tasks.sort(reverse=True, key=getProgress)


class Task:
    name = ""
    progress = 0

    def __init__(self, n):
        self.name = n

    def addProgress(self, number):
        if number < 0:
            print("this should have been caught but here for good measure")
            return
        int(number)
        self.progress = number


def formatList(user):
    userToList[user].sortByProgress()  ## check
    startedStr = ""
    notstartedStr = ""
    index = 0
    for task in userToList[user].tasks:  # formatting strings
        index += 1
        if (task.progress == 0):
            notstartedStr += "\n " + str(index) + " | " + task.name
        else:
            startedStr += "\n " + str(
                index) + " | " + task.name + " -- [*" + str(
                    task.progress) + "% completed*]"
    if startedStr == "":  ## more checks so phrases/sentences make sense in embed
        startedStr = "\nNo tasks currently in progress"
    if notstartedStr == "" and index != 0:
        notstartedStr = "\nAll tasks have been started"
    elif notstartedStr == "" and index == 0:
        notstartedStr = "\nTake a break. There are no tasks that need to be worked on :)"
    lockedState = ""
    if userToList[user].isLocked:
        lockedState = "[*Locked*]"
    else:
        lockedState = "[*Unlocked*]"
    embed = discord.Embed(
        title=str(user) + "'s List",
        url="",
        description=lockedState + "\n*" + str(index) +
        " task(s)* \n\n:shamrock: **In-Progress**" + str(startedStr) +
        "\n\n:shamrock: **Not Yet Started**" + str(notstartedStr),
        color=discord.Colour.green())
    return embed


def markDone(taskNum):
    userToList[currentUser].sortByProgress()  ## check
    progress = userToList[currentUser].tasks[taskNum].progress
    poppedTask = userToList[currentUser].tasks.pop(taskNum).name
    string = "Congrats! [*" + poppedTask + "*] was marked done with *" + str(
        progress) + "%* completion!"
    return string


## EVENTS ##
@bot.event
async def on_message(message):  # purely exists to
    global currentUser
    currentUser = str(message.author)
    await bot.process_commands(message)


## COMMANDS ##
@bot.command()
async def list(ctx):
    if currentUser not in userToList:
        userToList[currentUser] = List()
        #userToCompleted[currentUser] = List() might be implemented in the future
        await ctx.send(
            "Your list was created! It starts as being locked but you can unlock it with !unlock -- Try adding a task with `!addtask <task_name>`"
        )
    else:
        embed = formatList(currentUser)
        await ctx.send(embed=embed)


@bot.command()
async def showlist(ctx, *, otherUser):
    if str(otherUser) not in userToList:
        await ctx.send(
            "Sorry, I couldn't find the who you were looking for. If you typed their discord handle correctly (username#1234), they might've not created a list yet. Typing `!addtask <task_name>` or `!list` will create a list for them`"
        )
    else:
        embed = formatList(otherUser)
        await ctx.send(embed=embed)


@bot.command()
async def addtask(ctx, *, taskString):  # records task to user's list
    if currentUser not in userToList:
        userToList[currentUser] = List()
        #userToCompleted[currentUser] = List() might be implemented in the future
    taskList = taskString.split(',')
    addedTasks = ""
    for task in taskList:  # adds to tasks and to reformatted string
        if task != "":
            task = task.strip().capitalize()
            addedTasks += "  [*" + task + "*]"
            userToList[currentUser].addTask(task)
    userToList[currentUser].sortByProgress()
    embed = formatList(currentUser)
    await ctx.send(embed=embed)
    await ctx.send("Successfully added:" + addedTasks)


@bot.command()
async def givetask(ctx, *, taskString):  # records task to user's list
    taskList = taskString.split(',')
    taskList[0] = taskList[0].strip()
    if taskList[0] not in userToList:
        await ctx.send(
            "Sorry, I couldn't find the who you were looking for. If you typed their discord handle correctly (username#1234), they might've not created a list yet. Typing `!addtask <task_name>` or `!list` will create a list for them`"
        )
        return
    otherUser = taskList[
        0]  # keeps track of the person who's list you're adding to
    taskList.pop(0)
    addedTasks = ""
    if userToList[otherUser].isLocked == True and currentUser != otherUser:
      await ctx.send("Sorry, but this person has their list set to locked currently") 
    else:
      for task in taskList:  # adds to tasks and to reformatted string
          if task != "":
              task = task.strip().capitalize()
              addedTasks += "  [*" + task + "*]"
              userToList[otherUser].addTask(task)
      userToList[otherUser].sortByProgress()
      embed = formatList(otherUser)
      await ctx.send(embed=embed)
      await ctx.send("Successfully gave task to " + otherUser + ":" +
                     addedTasks)


@bot.command()
async def progress(ctx, taskNum, progress):
    taskNum = int(taskNum.strip()) - 1
    progress = int(progress.strip())
    if currentUser not in userToList:
        await ctx.send(
            "You don't seem to have a list yet -- Feel free to create one using `!addtask <task_name>` or an empty one using `!list`"
        )
        return
    elif taskNum < 0 or taskNum >= len(userToList[currentUser].tasks):
        await ctx.send("[" + str(taskNum + 1) +
                       "] doesn't correspond to any task in the list currently"
                       )
        return
    elif progress < 0:
        await ctx.send(
            str(progress) +
            " is not within the range of progress accepted (which is any number greater than or equal to 0)"
        )
        return
    elif progress >= 100:
        userToList[currentUser].tasks[taskNum].addProgress(progress)
        embed = formatList(currentUser)
        await ctx.send(embed=embed)
        await ctx.send(markDone(taskNum))
    else:
        userToList[currentUser].tasks[taskNum].addProgress(progress)
        embed = formatList(currentUser)
        await ctx.send(embed=embed)
        await ctx.send("[*" + userToList[currentUser].tasks[taskNum].name +
                       "*] set to *" + str(progress) + "%* done")


@bot.command()
async def droptask(ctx, *, toDropString):  # deletes tasks at these indexes
    if currentUser not in userToList:
        await ctx.send(
            "You don't seem to have a list yet -- Feel free to create one using `!addtask <task_name>` or an empty one using `!list`"
        )
        return
    toDropList = toDropString.split(',')  # reformatting string
    tasksNotFound = ""
    tasksDropped = ""
    for i in range(len(toDropList)):
        toDropList[i] = toDropList[i].strip()
        if toDropList[i] == "":
            continue
        else:
            toDropList[i] = (int(toDropList[i]) - 1
                             )  # index begins at 0 while list at 1
            print(toDropList[i])
            if toDropList[i] > -1 and toDropList[i] < len(
                    userToList[currentUser].tasks):
                tasksDropped = tasksDropped + "  [*" + userToList[
                    currentUser].tasks[
                        toDropList[i]].name + "*]"  # purely for formatting
                userToList[currentUser].tasks[toDropList[
                    i]].name = "!:+remove+:! " + userToList[currentUser].tasks[
                        toDropList[
                            i]].name  # marks tasks to be deleted to NOT mess up list order
            else:
                tasksNotFound = tasksNotFound + " [" + str(
                    toDropList[i] + 1) + "]"  # purely for formatting
    newList = []
    for task in userToList[
            currentUser].tasks:  # if task starts with keyword, it's deleted
        if task.name.startswith("!:+remove+:! ") == False:
            newList.append(task)
            print("task name:" + task.name)
    userToList[currentUser].tasks = newList
    embed = formatList(currentUser)
    await ctx.send(embed=embed)
    if tasksDropped != "":
        await ctx.send("Successfully dropped:" + tasksDropped)
    if tasksNotFound != "":
        await ctx.send(
            "Sorry, these numbers did not correspond to any tasks in your list:"
            + tasksNotFound)


@bot.command()
async def lock(ctx):  # lock's list
    if currentUser not in userToList:
        await ctx.send(
            "You don't seem to have a list yet -- Feel free to create one using `!addtask <task_name>` or `!list`"
        )
    else:
        userToList[currentUser].isLocked = True
        await ctx.send(
            str(currentUser) +
            "'s list is now *locked*. Only you can add tasks to it")


@bot.command()
async def unlock(ctx):  # unlocks liss
    if currentUser not in userToList:
        await ctx.send(
            "You don't seem to have a list yet -- Feel free to create one using `!addtask <task_name>` or `!list`"
        )
    else:
        userToList[currentUser].isLocked = False
        await ctx.send(
            str(currentUser) +
            "'s list is now *unlocked*. Anyone else can add tasks to it")


### ============= ###
### TEXT / EMBEDS ###
### ============= ###

# WARNING: Code is NOT pretty to look at beyond this point ##


@bot.command()
async def help(ctx):  # sends a list of all available commands
    embed = discord.Embed(
        title="Commands",
        url="",
        description=  # goodness, this textbox is going to SUUUCK to add to
        "Hello, I'm StudyBot (or StuBo), a discord task manager app. If you would like more info on any command, type  `!info <general_command_name>` \n\n:blueberries: **More Help** \n`!info <command_name>` : Gives more info on commands (besides !help, !info, !tips) \n`!tips` : Sends a list of efficiency tips :) \n\n:blueberries: **Viewing Lists** \n`!list` : Creates a locked list if you don't have one. Otherwise, it sends the most updated version of your list \n`!showlist <username#1234>` : Sends the most updated list of the user if one exists. Using !showlist @username#1234 does NOT work \n\n:blueberries: **Task Actions** \n`!addtask <task_name>` : Creates a locked list if you do not have one and adds tasks to it \n`!addtask <task_name>, <task_name>` : Adds multiple tasks to your list. Be sure to separate each task with a comma (,)! \n`!progress <#_of_task> <progress/100>` : Records your progress (out of 100%) on the task that corresponds to the number you provide. This command has no commas \n`!droptask <#_of_task>` : Drops a task from your list that corresponds to its number in the list \n`!droptask <#_of_task>, <#_of_task>` : Drops multiple tasks in the list that correspond to the numbers provided. Be sure to separate each number with a comma (,)! \n\n:blueberries: **Permission-Related** \n`!lock` : Locks your list so only you can add to it \n`!unlock` : Unlocks your list so anyone can add to it \n`!givetask <username#1234>, <task_name>` : Lets you add to someone else's list as long as it's unlocked. Like !addtask and !droptask, you can give multiple at once by separating the username and tasks with commas (very important)",
        color=discord.Color.blue())
    await ctx.send(embed=embed)


#############
@bot.command()
async def tips(ctx):  # a list of tips for efficiency
    embed = discord.Embed(
        title="Tips!",
        url="",
        description=
        ":hot_pepper: *Creating Lists* -- I'll create a locked list for you if you type !list or !addtask <task_name>. The only difference is that !list will create an empty one while !addtask will add stuff right off the bat. \n\n:hot_pepper: *Adding/removing multiple tasks from your list* -- Type the command once and separate all the task names or the task list numbers with a comma! I'll add/remove them all at once so you don't have to keep repeating yourself. This'll save some time and space in the discord channel :) \n \n :hot_pepper: *Using commas* -- For any multi-input command, commas are very important! StudyBot isn't exactly the smartest bot out there and won't separate different tasks if there's no comma in between them \n\n :hot_pepper: *Seeing others' lists* -- You can use !showlist <username#1234> to see a person's list. You have to copy/paste or type out the username! NOTE: This is NOT the nickname! This is the thing you see on the discord profile that is followed by a '#' and 4 numbers \n\n:hot_pepper: *Using channels to your advantage* -- Try using multiple channels to separate certain functions, like one just for updating progress and another for all task related commands. The progress command only allows you to update the progress on one task at a time. However, if you make significant progress on multiple tasks and update the list afterward, the channel might become congested with progress updates. \n\n:hot_pepper: *Creating User Specific Channels* -- If the team is small enough, you could create channels specific to each teammate or friend. You'd be able to see their newest list without overlap from other teammate lists. \n\n:hot_pepper: *Personal Use* -- You could always dm StuBo when he goes online in the discord server (he would have to be hosted on a private server so his lists wouldn't reset)",
        color=discord.Color.red())
    await ctx.send(embed=embed)


#############
@bot.command()
async def info(ctx, command):  # gives descriptions + ways to use commands
    if (command == "list"):  #list
        embed = discord.Embed(
            title="!list",
            url="",
            description=
            "Creates an empty list if you do not have one yet. However, if you do, I'll send the most updated version of your list in an embed. The list will start out locked (but you can easily unlock it using `!unlock`). My embed will show you whether it's locked/unlocked, how many tasks there are, the progress of the tasks you've started, and those that haven't yet been worked on.",
            color=discord.Color.teal())
        embed.add_field(name=":sauropod: Typing the Command", value="`!list`")
        await ctx.send(embed=embed)
    elif (command == "showlist"):
        embed = discord.Embed(
            title="!showlist",
            url="",
            description=
            "Let's you see the lists of another user (if one exists). I'll send the most updated version of their list in a embed. My embed will show you whether it's locked/unlocked, how many tasks there are, the progress of the tasks they've started, and those that haven't yet been worked on. @ing the user does not work. NOTE: This is NOT the nickname! This is the thing you see on their discord profile that is followed by a '#' and 4 numbers.",
            color=discord.Color.teal())
        embed.add_field(
            name=":sauropod: Typing the Command",
            value=
            "`!showlist username#1234` (BEWARE: @ing the user does not work, you have to type in the user's discord handle)"
        )
        await ctx.send(embed=embed)
    elif (command == "addtask"):  # addtask
        embed = discord.Embed(
            title="!addtask",
            url="",
            description=
            "Creates a locked list if you do not have one and allows you to add tasks to your ToDo list. If adding multiple tasks at once, remember to separate each task with a comma. Otherwise, I might accidentally combine them all into one task.",
            color=discord.Color.teal())
        embed.add_field(
            name=":sauropod: Using the Command",
            value=
            "`!addtask remember to hydrate` \n`!addtask english essay outline, clean desk, work on bot` (if adding multiple tasks)"
        )
        await ctx.send(embed=embed)
    elif (command == "droptask"):  # addtask
        embed = discord.Embed(
            title="!droptask <#_of_task>",
            url="",
            description=
            "Drops the task(s) associated with the number(s) provided as long as you have a list. If any numbers don't match, I'll send a message listing those that I wasn't able to figure out. You can input multiple task numbers in one command as long as they are separated by a comma (very inportant).",
            color=discord.Color.teal())
        embed.add_field(
            name=":sauropod: Using the Command",
            value=
            "`!droptask 4` (the number next to the task in the list is 4 in this example) \n`!droptask 2, 3, 6, 8` (if dropping multiple tasks)"
        )
        await ctx.send(embed=embed)
    elif (command == "lock"):  # lock
        embed = discord.Embed(
            title="!lock",
            url="",
            description=
            "Locks your list and prevents other users from adding tasks to it. This might be especially useful if this server isn't just for a team working on a project. No one besides you can add to it.",
            color=discord.Color.teal())
        embed.add_field(name=":sauropod: Typing the command", value="`!lock`")
        await ctx.send(embed=embed)
    elif (command == "unlock"):  # unlock
        embed = discord.Embed(
            title="!unlock",
            url="",
            description=
            "Unlocks your list and lets other users add tasks to it. This might be especially useful if you're part of a team working on a project. A project leader would be able to delegate tasks among members. But just remember that anyone can add to it.",
            color=discord.Color.teal())
        embed.add_field(name=":sauropod: Typing the command",
                        value="`!unlock`")
        await ctx.send(embed=embed)
    elif (command == "progress"):
        embed = discord.Embed(
            title="!progress",
            url="",
            description=
            "Records your progress on the corresponding task. The first number in the command tells me what task you want to update, while the second tells me how far along you've gotten (ie. you might've gotten 30% done with task #2). After recording your progress, I'll send you an updated version of your list with your updated progress. ",
            color=discord.Color.teal())
        embed.add_field(
            name=":sauropod: Using the command",
            value=
            "`!progress 3 80` (will record that you're 80% done with task #3)")
        await ctx.send(embed=embed)
    elif (command == "givetask"):  # addtask
        embed = discord.Embed(
            title="!give_task",
            url="",
            description=
            "Allows you to give other users tasks as long as their lists are unlocked (unless it's you giving yourself a task). Lists begin as locked so the user would have to !unlock their list before you can add to it. Commas are *very important* in this command so make sure to separate the user and all the tasks. Note: pinging the user does not work and you have to type out or copy/paste their full discord username (ie. username#1234).",
            color=discord.Color.teal())
        embed.add_field(
            name=":sauropod: Using the Command",
            value=
            "`!givetask username#1234, drink a cup of anarchy, thank StuBo for his dedication, start physics hw`  (commas are important)"
        )
        await ctx.send(embed=embed)
    else:
        await ctx.send(
            "Something went wrong... \n You might've written the command name wrong (or my creator forgot to add a description)."
        )


## TASKS ##
# dropTask(ctx, task # in list)
# newList(ctx, list name) -- actually it might get confusing as to which list you're adding to
# progress
# addProgress

bot.run(password)
