# Writing

> 完整串文归档（9 条）。返回 [线程索引](README.md)。

## How to write the Introduction?

原帖：<https://x.com/jbhuang0604/status/1638029709073166336> · 2023-03-21 · 共 20 条串文

How to write the Introduction?

As a junior student, writing the introduction of a research paper is arguably the most daunting part of paper writing. 😱

Here is a simple template I find useful:

3 Figures 🖼️ + 5 Questions 🤔

*🖼️ WHAT figure*

Start with the paper with a WHAT figure (known as the "teaser").

This figure shows only two things.
1⃣ Input
2⃣Output

This helps the readers understand what your work is about. Here are some of my favorite examples.

WHAT Example 1:

Mask R-CNN showcases its key results upfront without waiting until the result section.

1⃣ Input: Single images
2⃣Output: Instance segmentation masks

![image](media/1638029711359070208-1.jpg)

WHAT Example 2:

CycleGAN shows its ability to solve various unpaired image-to-image translation problems.

1⃣ Input: Images from domain A
2⃣Output: Images from domain B

![image](media/1638029713632313344-1.jpg)

WHAT Example 3:

Obstruction removal paper (https://alex04072000.github.io/SOLD/)
shows

1⃣ Input: Obstructed images (reflection, fence, raindrop)
2⃣Output: Clean images

Since the images are aligned, we can use split frames to 1) save space and 2) highlight the contrast.

![image](media/1638029715842768896-1.jpg)

相关链接：
- <https://alex04072000.github.io/SOLD/>

*🖼️ WHY figure*

This figure provides the "motivation" for your work.

The best WHY figure illustrates the existing work's core issue/problem with a concrete example.

Here are some of my favorite examples.

WHY Example 1:

The Shiftable Multiscale Transforms paper shows the NEED for translation invariance with a concrete example.

(a) Input signal
(b-d) Coefficients of wavelet representations.

(e) Shifted the input signal by ONE sample
(f-h) LOOK! Completely DIFFERENT coefficients

![image](media/1638029718724247555-1.jpg)

WHY Example 2

The Relative Attributes work highlights the NEED for a more informative and intuitive description using relative attributes with concrete examples.

![image](media/1638029720523616258-1.jpg)

WHY Example 3

The Feature Pyramid Networks work shows multiple alternative design options (a-c) and their drawbacks. This helps motivate the NEED for their design of a fast & accurate model.

![image](media/1638029722067116034-1.jpg)

*🖼️ HOW figure*

This figure describes how your method works.

Some tips:
✅ Link all sections
✅ Use consistent notations
✅ Self-contained caption
✅ Visualize the variables
✅ Cascade of small units: "Input -> some processing -> Output" (think about computational graph).

HOW Example 1:

The HyperReel paper (https://hyperreel.github.io/) visualizes the four main algorithmic steps.

Note the math notations, name, and detailed, self-contained figure caption.

![image](media/1638029724793307139-1.jpg)

相关链接：
- <https://hyperreel.github.io/>

HOW Example 2:

My video completion work back in my Ph.D. years https://filebox.ece.vt.edu/~jbhuang/project/vidcomp/
shows how the processing steps in each iteration.

![image](media/1638029727091892226-1.jpg)

相关链接：
- <https://filebox.ece.vt.edu/~jbhuang/project/vidcomp/>

HOW Example 3:

The Robust Dynamic Radiance Fields paper (https://robust-dynrf.github.io/) shows how all the math notations and variables connect with each other using this HOW figure. Note the descriptive figure caption.

![image](media/1638029729889501184-1.jpg)

相关链接：
- <https://robust-dynrf.github.io/>

With the WHAT-WHY-HOW figures, we are now ready to answer the following five questions!

🤔 What's the problem?
🤔 What have others done?
🤔 What's the gap?
🤔 What have you done?
🤔 What do you contribute?

*🤔 Q1: What's the problem?*

✅ State clearly what problem you are addressing.

✅ Tell the readers explicitly why they should care about the problem (e.g., applications).

🖼️ Use your WHAT figure for visual references.

*🤔 Q2: What have others done?*

✅ Describe what other solutions (SOTAs) are to your problem.

✅ Usually follows a historical trajectory, e.g., classical geometric methods did X, learning-based methods did Y, and recent hybrid methods did Z.

*🤔 Q3: What's the gap?*

✅ Explain why all these existing solutions are NOT satisfactory (in some aspects). This is important as your work often addresses a specific gap/flaw/drawback of existing work.

🖼️ Use the example in your WHY figure to illustrate the *gap*.

*🤔 Q4: What have you done?*

✅ Add "In this paper, ..." at the beginning of this paragraph. It helps provide a clean separation of the past/current work.

✅ Talk about a) Task, b) High-level idea, c) Evaluation

🖼️ Use your HOW figure to ground your discussions.

*🤔 Q5: What do you contribute?*

✅ Not everything you do is "novel" e.g., a large part of your work may build upon some existing methods. Thus, it is a good practice to explicitly state your contributions.

✅ Make a list so that lazy reviewers can use them in their reviews 😜

In sum, the introduction section would look like this:

🤔 What's the problem? (see 🖼️ WHAT figure)

🤔 What have others done?

🤔 What's the gap? (see 🖼️ WHY figure)

🤔 What have you done? (see 🖼️ HOW figure)

🤔 What do you contribute?

Hope this helps!

## How to write a paper that looks like a good one?

原帖：<https://x.com/jbhuang0604/status/1437443017510621185> · 2021-09-13 · 共 11 条串文

How to write a paper that looks like a good one?

You worked super hard and did great research, but somehow the reviewer 2 just doesn't buy it. Why? 🤔

It's probably because your paper does not look like a good paper *visually*. 🙄

How? 👇👇👇 #AcademicTwitter

*Figure 1: WHAT did you do?*

Nothing is more frustrating than not being able to figure out what the paper is about until page 5. 😠Show a TEASER figure on the very first page highlighting the inputs/outputs/key findings.

[![GIF 动画预览](media/1437443026461265924-1.jpg)](media/1437443026461265924-1.mp4)

▶ [GIF 动画（点击播放）](media/1437443026461265924-1.mp4)

*Figure 2: WHY did you do it?*

Motivate and justify the key insights/ideas of your work. It is often helpful to illustrate this more clearly by
1) SIMPLIFYING with a toy example and
2) CONTEXTUALIZING with prior work.

[![GIF 动画预览](media/1437443034384408579-1.jpg)](media/1437443034384408579-1.mp4)

▶ [GIF 动画（点击播放）](media/1437443034384408579-1.mp4)

*Figure 3: HOW did you do it?*

Show an *overview* figure on how your method works. Label everything so that it provides a clear roadmap of the entire paper.

[![GIF 动画预览](media/1437443042747822081-1.jpg)](media/1437443042747822081-1.mp4)

▶ [GIF 动画（点击播放）](media/1437443042747822081-1.mp4)

*Move figures/tables to the top*

Add "[!t]" parameter to your figure/table so that LaTeX will try placing them on the top of the page. Why?

Figures/tables are much easier to understand than reading plain texts. Moving them to the top helps readers quickly understand your work.

[![GIF 动画预览](media/1437443054353461252-1.jpg)](media/1437443054353461252-1.mp4)

▶ [GIF 动画（点击播放）](media/1437443054353461252-1.mp4)

*Self-contained figure/table caption*

Whatever you want to say for the figure/table, say them in the caption. It's annoying to find and match the corresponding texts describing the figure/table in your paper.

More on avoiding mental correspondence: https://x.com/jbhuang0604/status/1279992087497314305

> **引用 [@jbhuang0604](https://x.com/jbhuang0604)**：
>
> Sharing one idea I found useful for paper writing:
>
> Do NOT ask people to solve correspondence problems.
>
> Some Dos and Don'ts examples below:
>
> *Figures*: Don't ask people to match (a), (b), (c) ... with the descriptions in the figure caption. https://t.co/tc7f8pVZlk

[![GIF 动画预览](media/1437443062653927425-1.jpg)](media/1437443062653927425-1.mp4)

▶ [GIF 动画（点击播放）](media/1437443062653927425-1.mp4)

*Concise notations*

Use SINGLE letters for your math notations. Examples:
• Color_j -> C_j
• Net -> F(\cdot)

All the other descriptions should be within
\mathrm

[![GIF 动画预览](media/1437443075173912584-1.jpg)](media/1437443075173912584-1.mp4)

▶ [GIF 动画（点击播放）](media/1437443075173912584-1.mp4)

*Short titles*

Add titles (e.g., using \paragraph) to your figure/table captions and the main texts. They make your paper more structured and organized and help your readers navigate the paper with ease.

[![GIF 动画预览](media/1437443083612868613-1.jpg)](media/1437443083612868613-1.mp4)

▶ [GIF 动画（点击播放）](media/1437443083612868613-1.mp4)

*Clean table*

Follow simple design principles for making clean a table:
• no \line, use \toprule, \midrule, \bottomrule
• no vertical lines
• left align text
• center align numbers
• group and remove repetition with multirow/multicol

[![GIF 动画预览](media/1437443092114706432-1.jpg)](media/1437443092114706432-1.mp4)

▶ [GIF 动画（点击播放）](media/1437443092114706432-1.mp4)

*Avoid empty spaces*

Fill the paper into full page limit. It gives your readers a sense of a POLISHED and not RUSHED paper.

More on Deep Paper Gestalt: https://arxiv.org/abs/1812.08775

![image](media/1437443098938945536-1.jpg)

相关链接：
- <https://arxiv.org/abs/1812.08775>

Hope this helps! If your paper looks like a good paper, reads like a good paper, then it's probably a good paper.

Happy writing!

Any additional tips on making your papers look awesome?

### 作者补充回复

@Alberto_H9 I added one example for each of the three figures.

Figure 1 WHAT: https://x.com/jbhuang0604/status/1437560146612441089

Figure 2 WHY: https://x.com/jbhuang0604/status/1437562132279738372

Figure 3 HOW: https://x.com/jbhuang0604/status/1437563329455824905

<https://x.com/jbhuang0604/status/1437564308674781185>

@MattHemsley3 Glad that you like it!

[![GIF 动画预览](media/1437564600946397184-1.jpg)](media/1437564600946397184-1.mp4)

▶ [GIF 动画（点击播放）](media/1437564600946397184-1.mp4)

<https://x.com/jbhuang0604/status/1437564600946397184>

@themintsv Oh no...

[![GIF 动画预览](media/1437564898071007234-1.jpg)](media/1437564898071007234-1.mp4)

▶ [GIF 动画（点击播放）](media/1437564898071007234-1.mp4)

<https://x.com/jbhuang0604/status/1437564898071007234>

## How to write clear and concise sentences?

原帖：<https://x.com/jbhuang0604/status/1437931004451250176> · 2021-09-15 · 共 15 条串文

How to write clear and concise sentences?

Getting ready to write up your very first research paper? Writing a paper could be daunting, particularly for non-native English speakers. 😬😬😬 How can we avoid common mistakes in technical writing?

Check out the thread below! 🧵

*Active voice*

Friends don’t let friends use passive voice!

Using passive voice hides the subject and creates ambiguous, indirect, and wordy sentences. Things don't "get done" by themselves. Take responsibility for what you do and use active voice whenever possible.

[![视频预览](media/1437931021706612736-1.jpg)](media/1437931021706612736-1.mp4)

▶ [视频（点击播放）](media/1437931021706612736-1.mp4)

*Statements in positive form*

Tell your readers "what is" instead of "what is not".

not honest ➡️ dishonest
did not remember ➡️ forgot
did not pay any attention to ➡️ ignored
did not have much confidence in ➡️ distrusted

[![GIF 动画预览](media/1437931029759766534-1.jpg)](media/1437931029759766534-1.mp4)

▶ [GIF 动画（点击播放）](media/1437931029759766534-1.mp4)

*Which (non-restrictive) vs. That (restrictive)*

As a WHICH adjective clause is non-essential and non-defining, you go on a "which hunt" and break down long sentences with into simpler ones.

More on restrictive/non-restrictive adjective clauses: https://youtu.be/NjTM4booWHo

[![GIF 动画预览](media/1437931037372395522-1.jpg)](media/1437931037372395522-1.mp4)

▶ [GIF 动画（点击播放）](media/1437931037372395522-1.mp4)

相关链接：
- <https://youtu.be/NjTM4booWHo>

*Respectively*

Do not ask your readers to solve mental correspondence  problems. Revise the sentence to get rid of "respectively".

Example: https://x.com/jbhuang0604/status/1279992094577352704?s=20

> **引用 [@jbhuang0604](https://x.com/jbhuang0604)**：
>
> *Respectively*
>
> It's hard to parse which corresponds to which in the sentence that ends with "respectively" (have to solve a long-range correspondence problem). Break them them so that one sentence talks about one thing. https://t.co/GLZWhjxlEx

[![GIF 动画预览](media/1437931050278309888-1.jpg)](media/1437931050278309888-1.mp4)

▶ [GIF 动画（点击播放）](media/1437931050278309888-1.mp4)

*Fancy words*

I used to think using fancy words make the paper more "academic", but I now prefer simplicity and clarity.

utilize ➡️ use
initiate ➡️ begin
terminate ➡️ end
ascertain ➡️ find out
constitute ➡️ make up
disintegrate ➡️ break down

[![GIF 动画预览](media/1437931059048501249-1.jpg)](media/1437931059048501249-1.mp4)

▶ [GIF 动画（点击播放）](media/1437931059048501249-1.mp4)

*Needless words*

Replacing needless words with simple ones!

at the time when ➡️ when
owing to the fact that ➡️ since
in spite of the fact that ➡️ though
the reason why is that ➡️ because
this is a subject that ➡️ this subject
the question as to whether or not ➡️ whether

[![GIF 动画预览](media/1437931071446847496-1.jpg)](media/1437931071446847496-1.mp4)

▶ [GIF 动画（点击播放）](media/1437931071446847496-1.mp4)

*Remove vague pronoun references*

Find and remove all the ambiguous pronoun references in your paper, e.g., that, this, it, these, those.

Replace these vague pronoun references with SPECIFIC noun or noun phrase.

[![GIF 动画预览](media/1437931079286116352-1.jpg)](media/1437931079286116352-1.mp4)

▶ [GIF 动画（点击播放）](media/1437931079286116352-1.mp4)

*Few / A few / Quite a few*

Be specific about the quantity you intend to describe.

A few = Some (not many but some)
Few = "Only" a few (a small number of)
Quite a few = Many

[![GIF 动画预览](media/1437931087548780544-1.jpg)](media/1437931087548780544-1.mp4)

▶ [GIF 动画（点击播放）](media/1437931087548780544-1.mp4)

*Note that*

Avoid "Note that" and "It should be noted that." Readers don't like to be frequently reminded to pay attention.

[![GIF 动画预览](media/1437931095589326852-1.jpg)](media/1437931095589326852-1.mp4)

▶ [GIF 动画（点击播放）](media/1437931095589326852-1.mp4)

*Resources*

Check out many wonderful writing advices on the web!

http://www.jlakes.org/ch/web/The-elements-of-style.pdf

https://vision.sjtu.edu.cn/writing.html

https://taoxie.cs.illinois.edu/advice.htm

相关链接：
- <http://www.jlakes.org/ch/web/The-elements-of-style.pdf>
- <https://vision.sjtu.edu.cn/writing.html>
- <https://taoxie.cs.illinois.edu/advice.htm>

That's all (for now)!

Would love to learn more about your favorite tips on writing clearly and concisely!

*Case*

Often redundant!

Before: In many cases, the rooms lacked air conditioning.
After: Many of the rooms lacked air conditioning.

Before: It has rarely been case that any mistake has been made.
After: Few mistakes have been made.

Source: The Elements of Style

[![GIF 动画预览](media/1437986944257036290-1.jpg)](media/1437986944257036290-1.mp4)

▶ [GIF 动画（点击播放）](media/1437986944257036290-1.mp4)

*However*

We often use "however" as "nevertheless/in spite of that" in a paper. Do NOT start with a sentence with however to avoid confusion. Why?

When starting with however, it means "in whatever manner/way" or "to whatever degree/extent".

[![GIF 动画预览](media/1437986953262141443-1.jpg)](media/1437986953262141443-1.mp4)

▶ [GIF 动画（点击播放）](media/1437986953262141443-1.mp4)

*Transitions*

Use transitions to connect sentences.

• Space: above, below, inside

• Cause and effect: as a result, because, since

• Similarity: as, likewise, similarly

• Contrast: although, however, on the other hand, in contrast

Source: https://stanford.edu/class/ee267/WIM/writing_style_guide.pdf

[![GIF 动画预览](media/1437986960921042948-1.jpg)](media/1437986960921042948-1.mp4)

▶ [GIF 动画（点击播放）](media/1437986960921042948-1.mp4)

相关链接：
- <https://stanford.edu/class/ee267/WIM/writing_style_guide.pdf>

## How to draw an overview figure?

原帖：<https://x.com/jbhuang0604/status/1665738070002483201> · 2023-06-05 · 共 14 条串文

How to draw an overview figure?

Creating a clear and informative overview figure is crucial for visualizing HOW your method works.

But how? 🤔 Let's deep dive with 🐢

![image](media/1665738070002483201-1.jpg)

*Choose the right level of abstraction*

Simplifying complex procedures helps improve clarity.

Ask yourself what the key message you want to convey. Don't overwhelm your readers with unnecessary details.

![image](media/1665738072196096003-1.jpg)

*Think in terms of computational graph*

Most methods process some INPUT with some COMPUTATION to produce some OUTPUT.

Visualize the flow with a "computational graph".

• Nodes: Computation
• Arrows: Dependency

![image](media/1665738074964258817-1.jpg)

*Use an example*

While your overview figure illustrates an *abstract* workflow, visualizing the intermediate variables/data with a *concrete* example makes it easier to understand.

![image](media/1665738077552140288-1.jpg)

*Follow the left-to-right direction*

Most languages read from left to right. ⏩⏩

Following this direction makes your figure "read" better.

![image](media/1665738080052027393-1.jpg)

*Apply formatting strategically*

Be purposeful when you use formatting to highlight similarity, grouping, and contrast.

Make sure that you don't overdo it.

![image](media/1665738082321039364-1.jpg)

*Use proper font size*

Use consistent and clearly visible font size.

Don't make your overview figure a vision test. 🧐

![image](media/1665738085202640897-1.jpg)

*Use consistent formatting*

• Capitalize the first character for the first word?
• Capitalize the first character for every word?
• All caps?
• All lowercase?

Pick one and stick with it.

![image](media/1665738087744299008-1.jpg)

*Align everything*

Tiny bits of misalignment here and there distract your readers. (Look how annoying this looks like!)

Align the positions, spacing, and sizes.

![image](media/1665738090395193346-1.jpg)

*Use consistent styles*

Put the label
• below the image?
• above the image?
• within the image?
• to the right of the image?

Pick one and be consistent.

![image](media/1665738093121421314-1.jpg)

*Provide a roadmap for the paper*

Add labels for sections, equations, and figures to provide a roadmap for the paper.

![image](media/1665738095965229061-1.jpg)

*Be explicit about the dependency/computation*

When you merge two arrows, it's unclear what happened there.

Did you add/subtract/multiply/max/min/some other things? Or does the DO SOMETHING module take two separate inputs? Make it explicit!

![image](media/1665738098519556099-1.jpg)

*Avoid overloading the interface*

Here the DO SOMETHING module takes only ONE single input.

The example above obscures this process (it looks like the module takes two inputs simultaneously).

![image](media/1665738101111521281-1.jpg)

I am not a designer, but these tips have helped me improve the clarity of my work.

Hope you will find them useful as well!

What are your favorite tips for creating an overview figure?

## How to create a good table?

原帖：<https://x.com/jbhuang0604/status/1626372600824844289> · 2023-02-17 · 共 8 条串文

How to create a good table?

While in grad school, I thought my job writing the paper was done after dumping all the numerical numbers from my experiments in a table. 🤦‍♂️

Check out some tips that will help you improve the quality of your tables! 🧵

*1⃣ Avoid vertical lines*

Having vertical lines in a table almost always makes the table less readable. Avoid them at all costs.

![image](media/1626372602259206144-1.jpg)

*2⃣ Never, ever use double rules*

Feel the urge to use double rules (\hline)?

Try the \toprule, \midrule, \bottomrule using the booktabs package instead! It levels up your table in no time!

![image](media/1626372604440326145-1.jpg)

*3⃣ Label the columns*

Add up/down arrows to let readers know how to interpret the numbers.

Add units to let your readers understand what the numbers mean.

![image](media/1626372606596206593-1.jpg)

*4⃣ Align everything*

• Align texts to the left
• Align numbers to the center
• Align numbers at consistent decimal point

![image](media/1626372608747864065-1.jpg)

*5⃣ Grouping results*

Have two or more groups of results and feel the urge again to separate them using vertical lines?

\multicolumn comes to the rescue!

Remember to use \cmidrule to group the right columns!

![image](media/1626372611163684867-1.jpg)

*6⃣ Encode rows with attributes*

One table, one message. Don't mix all the results together.

If possible, encode different rows using *attributes* so that it's easy for readers to understand/compare results from different rows.

![image](media/1626372613441290240-1.jpg)

Hope this helps!

Having a clean and clear table definitely gets your message across more effectively!

What's your favorite tip on creating tables?

### 作者补充回复

@ccrommel Figures are good for showing the *general trend*.
Tables are good for showing *specific numbers*.

Your tables can easily be re-used in the follow-up work, but not your figures.

<https://x.com/jbhuang0604/status/1626813373537984512>

## How to write math in a paper?

原帖：<https://x.com/jbhuang0604/status/1643118681960923137> · 2023-04-04 · 共 11 条串文

How to write math in a paper?

Math allows you to convey your idea precisely and concisely. But how to write them clearly? 🤔

Check out some high-level tips (with examples). 🧵

*Make it readable*

Math writing blends both NATURAL and MATH languages. It should be *readable*.

![image](media/1643118683231776770-1.jpg)

*Follow good style*

• texts in math: \mathrm for
• transpose: use ^\top instead of ^T
• big parentheses: use \left and \right

![image](media/1643118685073166337-1.jpg)

*Refer to notation together with their name*

Nothing is more frustrating than flipping pages to figure out what your notations mean.

![image](media/1643118686813794304-1.jpg)

*Name every equation*

Your readers will thank you!

![image](media/1643118688504107010-1.jpg)

*Write in a consistent format*

Reduce the mental load of your readers.

![image](media/1643118690487943170-1.jpg)

*Avoid redundant notation*

If you will not use them again, you don't need to introduce unnecessary notations.

![image](media/1643118692367052800-1.jpg)

*Define notation & macros*

Use descriptive names as your macros.
It helps avoid notation inconsistency in your paper.

![image](media/1643118694199963648-1.jpg)

*Simplify notation*

e.g., avoid parenthesized indexes

![image](media/1643118695881879552-1.jpg)

*Use negative numbers correctly*

The "-" is interpreted as a hyphen by your LaTeX editor. Use $-1$ instead.

![image](media/1643118697421127684-1.jpg)

Resources/References:

Check out the excellent resources here!
https://www.robots.ox.ac.uk/~phst/Style/Ten_Rules.pdf

https://cs.dartmouth.edu/~wjarosz/writing.md.html

https://www.ece.ucdavis.edu/~jowens/commonerrors.html

https://people.csail.mit.edu/fredo/PUBLI/writing.pdf

相关链接：
- <https://www.robots.ox.ac.uk/~phst/Style/Ten_Rules.pdf>
- <https://cs.dartmouth.edu/~wjarosz/writing.md.html>
- <https://www.ece.ucdavis.edu/~jowens/commonerrors.html>
- <https://people.csail.mit.edu/fredo/PUBLI/writing.pdf>

## How to prepare journal response letter?

原帖：<https://x.com/jbhuang0604/status/1387148974377865219> · 2021-04-27 · 共 7 条串文

Sharing ideas on writing revision response letters.

When submitting a paper to a journal, almost surely you will get a major/minor revision recommendation from the associated editor. How should we respond?

Check out the examples https://www.overleaf.com/read/ccjtfbxcnvkv
and some tips 💡below

相关链接：
- <https://www.overleaf.com/read/ccjtfbxcnvkv>
- <https://t.co/AWdUUbU3nd> — Overleaf, Online LaTeX Editor

*Just do it*

Unlike rebuttals for conferences where you promise the changes you WILL include, response letters for journals should show what the changes you ALREADY DID.

Respect the reviewers' time and follow the core principles to make it clear, self-contained, and thorough.

[![GIF 动画预览](media/1387148982753939467-1.jpg)](media/1387148982753939467-1.mp4)

▶ [GIF 动画（点击播放）](media/1387148982753939467-1.mp4)

*One comment/question at a time*

Very often reviewers may write comments with several long paragraphs. Parse and organize the comments into "bite-sized" questions so you can respond directly with evidence support.

[![GIF 动画预览](media/1387148991410974723-1.jpg)](media/1387148991410974723-1.mp4)

▶ [GIF 动画（点击播放）](media/1387148991410974723-1.mp4)

*Be thorough*

Properly address ALL the comments from the reviewers, even for comments you don't agree with (e.g., explain why you cannot add X baseline, run on Y dataset). Failing to do so leads to unnecessary delays for your papers.

[![GIF 动画预览](media/1387148999531143171-1.jpg)](media/1387148999531143171-1.mp4)

▶ [GIF 动画（点击播放）](media/1387148999531143171-1.mp4)

*Self-contained*

• New figures/tables? Add them to the response letter.
• Revised texts? Show the texts *before* and *after* your revision.
• Include a manuscript with highlighted changes.

Don't ask reviewers to solve mental correspondence.

https://x.com/jbhuang0604/status/1279992087497314305?s=20

> **引用 [@jbhuang0604](https://x.com/jbhuang0604)**：
>
> Sharing one idea I found useful for paper writing:
>
> Do NOT ask people to solve correspondence problems.
>
> Some Dos and Don'ts examples below:
>
> *Figures*: Don't ask people to match (a), (b), (c) ... with the descriptions in the figure caption. https://t.co/tc7f8pVZlk

*Be proactive*

Q from R2: How did you set the value $K$? Sensitivity matters.

Lvl 1: Empirically.
Lvl 2: We choose K via cross-validation.
Lvl 3: Show the entire process. Comment on the sensitivity of the value of K on the validation set.

[![视频预览](media/1387149035635625992-1.jpg)](media/1387149035635625992-1.mp4)

▶ [视频（点击播放）](media/1387149035635625992-1.mp4)

*Be polite and professional*

Treat reviewers as your colleagues who help you improve your work. Very often they help point out flaws and provide valuable suggestions. Thank them.

[![GIF 动画预览](media/1387149045030850560-1.jpg)](media/1387149045030850560-1.mp4)

▶ [GIF 动画（点击播放）](media/1387149045030850560-1.mp4)

## How to prepare supplementary material?

原帖：<https://x.com/jbhuang0604/status/1592563395936817154> · 2022-11-15 · 共 7 条串文

How to prepare supplementary material?

Accompanying your paper submissions with supp material has become standard. But why/what/how to prepare good supplementary material remain unclear to many junior students. 😕

Sharing some ideas below 🧵

*Why supplementary material?*

When R2 reviews your paper, the only question in their mind is:

"HOW CAN I KILL THIS PAPER? 🧐"

• Unclear exposition?
• Insufficient details?
• Unconvincing validation?

Don't give them any reason.

[![GIF 动画预览](media/1592563402819661824-1.jpg)](media/1592563402819661824-1.mp4)

▶ [GIF 动画（点击播放）](media/1592563402819661824-1.mp4)

*What? - Exposition*

Unable to explain your work well in the main paper due to the page limit?

Anticipate the questions! Including additional figures, tables, proof, and algorithms in your supp material helps tremendously alleviate all these issues.

[![GIF 动画预览](media/1592563410725900290-1.jpg)](media/1592563410725900290-1.mp4)

▶ [GIF 动画（点击播放）](media/1592563410725900290-1.mp4)

*What? - Details*

Reproducibility is one major concern of every reviewer.

Provide sufficient implementation details of your method, data, methodology, and evaluation protocol so that everyone can reproduce your findings.

[![GIF 动画预览](media/1592563418573045762-1.jpg)](media/1592563418573045762-1.mp4)

▶ [GIF 动画（点击播放）](media/1592563418573045762-1.mp4)

*What? - Validation*

A paper may not be the right format to best present the experimental validation.

For example, you should definitely show video results (not sampled frames) if you work on video.

Showing images of video is like showing a 1D scanline of an image!

[![GIF 动画预览](media/1592563430267187201-1.jpg)](media/1592563430267187201-1.mp4)

▶ [GIF 动画（点击播放）](media/1592563430267187201-1.mp4)

*How? - Organization*

Don't simply brain-dump all the contents without a clear organization.

Personally, I am a big fan of organizing all the results via local (no external links) HTML files. I found interactive browsing very convenient.

https://alex04072000.github.io/SOLD/website/Obstruction_HTML_CameraReady/result.html

[![GIF 动画预览](media/1592563438320234496-1.jpg)](media/1592563438320234496-1.mp4)

▶ [GIF 动画（点击播放）](media/1592563438320234496-1.mp4)

相关链接：
- <https://alex04072000.github.io/SOLD/website/Obstruction_HTML_CameraReady/result.html>

Hope this gives you some initial ideas on how you can prepare your supplementary material!

Good luck with your paper submission!

![image](media/1592563443478851584-1.jpg)

## How to cite papers?

原帖：<https://x.com/jbhuang0604/status/1672342931473137664> · 2023-06-23 · 共 10 条串文

How to cite papers?

Citing papers properly
👉 gives credit where credit's due,
👉 provides supporting evidence of your claim, and
👉 presents an organized view of related work.

Sharing some tips I found useful. 🧵

![image](media/1672342931473137664-1.png)

*Parenthetical citations*

"Parenthetical": removing the citations, your sentences should still make sense.

When writing the related work, focus on the STORY and cite relevant papers along the way.

This provides an organized structure of how individual papers are connected.

[![GIF 动画预览](media/1672342941275398145-1.jpg)](media/1672342941275398145-1.mp4)

▶ [GIF 动画（点击播放）](media/1672342941275398145-1.mp4)

*Narrative citations*

This style often starts with authors' name in your sentence.

Examples: A et al. propose X. B et al. explore Y.

Pro: Useful if you want to highlight a particular work.

Con: Easily leads to a poorly written "laundry list".

[![GIF 动画预览](media/1672342953329557504-1.jpg)](media/1672342953329557504-1.mp4)

▶ [GIF 动画（点击播放）](media/1672342953329557504-1.mp4)

*Grouping citations*

Avoid adding a looong list of citations without meaningful grouping.

❌ Recent work extends X to improve speed, quality, and memory efficiency [1, 2, 3, 4].

✅ Recent work extends X to improve speed [1], quality [2, 3], and memory efficiency [4].

[![GIF 动画预览](media/1672342961730863107-1.jpg)](media/1672342961730863107-1.mp4)

▶ [GIF 动画（点击播放）](media/1672342961730863107-1.mp4)

*Repetitive citations*

It's okay to cite the papers whenever appropriate, e.g., citing methods/datasets in your tables.

No one can remember all these acronyms. 🥱

[![GIF 动画预览](media/1672342970098413569-1.jpg)](media/1672342970098413569-1.mp4)

▶ [GIF 动画（点击播放）](media/1672342970098413569-1.mp4)

*Broad citations*

If possible, cite relevant papers more broadly. Giving others credit does not hurt yours.

Live view of authors finding their work is not cited in your paper:

[![GIF 动画预览](media/1672342978554216449-1.jpg)](media/1672342978554216449-1.mp4)

▶ [GIF 动画（点击播放）](media/1672342978554216449-1.mp4)

*BibTeX formatting (conference/Journal)*

Never trust BibTeX downloaded from Google Scholar.

They suck!

Manually correct those entries.

conference 👉 inproceedings
conference 👉 article

[![GIF 动画预览](media/1672342986921844737-1.jpg)](media/1672342986921844737-1.mp4)

▶ [GIF 动画（点击播放）](media/1672342986921844737-1.mp4)

*BibTeX formatting (label)*

I find the style of labels
<FirstAuthorLastName><Year><FirstWord> easy to use.

 Never use the BibTeX label from dblp.

They suck!

You will have a hard time knowing which papers you are citing. 🥴

[![GIF 动画预览](media/1672342995281084417-1.jpg)](media/1672342995281084417-1.mp4)

▶ [GIF 动画（点击播放）](media/1672342995281084417-1.mp4)

*BibTeX formatting (macros)*

BibTeX offers macros to help standardize your citations.

Use them for frequently cited conferences/journals to cite them consistently throughout your paper.

[![GIF 动画预览](media/1672343003665510401-1.jpg)](media/1672343003665510401-1.mp4)

▶ [GIF 动画（点击播放）](media/1672343003665510401-1.mp4)

*BibTeX formatting (capital letters)*

BibTeX is case-sensitive. Be cautious when entering author names, titles, and journal names.

Use curly braces {} to preserve capitalization when needed.

[![GIF 动画预览](media/1672343012087668740-1.jpg)](media/1672343012087668740-1.mp4)

▶ [GIF 动画（点击播放）](media/1672343012087668740-1.mp4)
