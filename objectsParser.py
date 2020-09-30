from utills import ObjectIter
from PDFObjects import *
from typing import Iterable, List

SEPERATORS = b"\\/[]<>() \t\n"


def extract_name(stream: ObjectIter) -> str:
    """
    Extracts the next name from the iterator (7.3.5 PDF 32000-1:2008)
    :param stream:A stream whose forward slash / was just consumed
    :return: String containing the name
    """
    out_string = b"/"
    for letter in stream:
        if (letter in SEPERATORS):
            stream.prev()  # Reverts a step back to where
            # the name ended in order for the typechecker to deduce the type
            break
        out_string += letter
    return out_string


def skip_space(stream: ObjectIter) -> str:
    """
    Moves stream to the next non whitespace char
    :param stream: Any iterable object
    :return: First letter after the whitespace
    """
    peek = stream.peek(1)
    if (not peek.isspace() or peek == b""):
        return ""

    for i in stream:

        if (not i.isspace()):
            stream.prev()
            return ""


def parse_string_literal(stream: ObjectIter) -> str:
    """
    Parses string literals (7.3.4.2) PDF 32000-1:2008
    :param stream: A stream whose opening round bracket ( was just consumed
    :return: The string literal including the round brackets
    """
    out_string = b"("
    countOpeningBraces = 1
    countClosingBraces = 0
    for letter in stream:
        if countClosingBraces == countOpeningBraces:
            break
        if letter == b"(":
            countOpeningBraces += 1
        elif letter == b")":
            countClosingBraces += 1
        out_string += letter
    stream.prev()
    return out_string


def parse_numeric(init: str, stream: ObjectIter):
    number: str = init
    for char in stream:
        if (char in b"\\/[]<>()\t\n"):
            stream.prev()
            break
        elif (char == b" "):
            upcomingchars = stream.peek(3)
            isRef = upcomingchars == b"0 R"
            if (isRef):
                stream.move_poiter(3)
                return IndirectObjectRef(number)
            else:
                return number
        elif (not char.isdigit() and char != b"."):
            number += stream.finishNumber()
            break
        number += char
    return number


def parse_stream(streamIter: ObjectIter, letter=None):
    if (letter is None):
        letter = next(streamIter)

    debug = letter.decode("utf-8")
    if letter == b"/":
        value = extract_name(streamIter)

    elif letter == b"[":
        value = extract_array(streamIter)

    elif letter.isdigit() or letter == b"-":
        value = parse_numeric(letter, streamIter)

    elif letter == b"<":
        letter = next(streamIter)
        if letter == b"<":
            value = parse_dictionary(streamIter)
        else:
            value = b"<" + letter + streamIter.moveto(b">") + b">"
            try:
                next(streamIter)
            except StopIteration:
                return value

    elif letter == b"(":
        value = parse_string_literal(streamIter)
    elif letter in b"tf":  # handels true/false
        value = letter + streamIter.moveto(b"e") + next(streamIter)
    elif letter == b"n":  # handels null values
        peek = streamIter.peek(3)
        if (peek == b"ull"):
            value = b"null"
            streamIter.move_poiter(3)

    skip_space(streamIter)

    return value


def parse_dictionary(pdf_stream):
    object_dict = dict()
    streamIter = ObjectIter(pdf_stream) if type(pdf_stream) != ObjectIter else pdf_stream
    streamIter.prepareDictParse()
    for letter in streamIter:
        # Parse Key

        if letter == b">":
            letter = next(streamIter)
            if (letter == b">"):
                return PDFDict(object_dict)

        elif letter != b"/":
            raise AssertionError(f"Expected a forward slash / to build a dict key but got {letter}")
        key = extract_name(streamIter)
        skip_space(streamIter)
        letter = next(streamIter)
        # parse value
        value = parse_stream(streamIter, letter)

        object_dict[key] = value

    return PDFDict(object_dict)


def extract_array(stream: Iterable) -> List[str]:
    out_string = b""
    count_closingBraces = 0
    count_openingBraces = 1

    for letter in stream:
        if letter == b"]":
            count_closingBraces += 1
        elif letter == b"[":
            count_openingBraces += 1
        if count_closingBraces==count_openingBraces:
            break
        out_string += letter

    return PDFArray(parse_arrayObjects(out_string))


def parse_arrayObjects(array_str: bytes):
    stream_iter = ObjectIter(array_str)
    array = []
    for char in stream_iter:
        if (char.isspace()):
            continue
        item = parse_stream(stream_iter, char)
        array.append(item)

    return array


if __name__ == '__main__':
    ##Bad table
    t1 = b"""/Type/Annot/Border[ 0 0 0]/Dest[ 4863 0 R/XYZ 76.450073 383.27719 0]/F 4/Rect[ 167.25 565.5 447.75 582]/Subtype/Link>>"""
    t1 = parse_dictionary(t1)

    t2 = b"5 15"
    e2 = ObjectIter(t2)

    print(e2.peek(5))
    print(e2.peek(2))
    print(e2.peek(2))

    t5 = parse_stream(ObjectIter(b"[ 167.25 565.5 447.75 582]"))
    print(t5)

    t2 = parse_arrayObjects(t2)

    parse_arrayObjects(b'<F6BF5D976038EA4C968074C82AB159D8><3B6F6B904D0C5440BCE35DB1FD6F6BAF>')

    # print(parse_stream(ObjectIter(b'<</BaseFont/JIDMBG+MonotypeSorts/CIDSystemInfo 299 0 R/CIDToGIDMap/Identity/DW 1000/FontDescriptor 300 0 R/Subtype/CIDFontType2/Type/Font/W[81[761]]>>\r')))

    print(parse_dictionary(b"<<>>"))

    # print(parse_stream(ObjectIter(b'<</BitsPerComponent 8/ColorSpace 282 0 R/DecodeParms[<<>>]/Filter[/DCTDecode]/Height 187/Length 2912/Subtype/Image/Type/XObject/Width 187>>')))
    # t2 = """/Subtype/Image
    # /ColorSpace/DeviceGray
    # /Width 360
    # /Height 135
    # /BitsPerComponent 8
    # /Filter/DCTDecode/Length 6899>>"""
    #
    # print(parseDict(t2))
    # t1 = (
    #     rf"""/Type/Page/BleedBox[ 0 0 504 661.5]/Contents 5 0 R/CropBox[ 0 0 504 661.5]/MediaBox[ 0 0 504 661.5]/Parent 3493 0 R/Resources<</Font<</F3 2186 0 R>>/ProcSet[/Text/ImageC]>>/Rotate 0/Trans<<>>>>""")

    e2 = b"""<<
/Limits [705 768]
/Nums [705 3762 0 R 706 3763 0 R 707 3764 0 R 708 3765 0 R 709 3766 0 R
710 3767 0 R 711 3768 0 R 712 3769 0 R 713 3770 0 R 714 3770 0 R
715 [3771 0 R 3772 0 R 3773 0 R 3774 0 R 3775 0 R 3776 0 R 3777 0 R 3778 0 R 3779 0 R 3780 0 R
3781 0 R 3782 0 R 3783 0 R 3784 0 R 3785 0 R 3786 0 R 3787 0 R 3788 0 R 3789 0 R 3790 0 R
3791 0 R 3792 0 R 3793 0 R 3794 0 R 3795 0 R 3796 0 R null 3797 0 R 3798 0 R 3799 0 R
3800 0 R 3801 0 R 3802 0 R 3803 0 R 2373 0 R]
 716 3804 0 R 717 3805 0 R 718 3806 0 R 719 3807 0 R
720 3808 0 R 721 [3809 0 R 3810 0 R 3811 0 R 3812 0 R 3813 0 R 3814 0 R 3815 0 R 3816 0 R 3817 0 R 3818 0 R
3819 0 R 3820 0 R 3821 0 R 3822 0 R 3823 0 R 3824 0 R 3825 0 R 3826 0 R 3827 0 R 3828 0 R
3829 0 R 3830 0 R 3831 0 R 3832 0 R 3833 0 R 3834 0 R 3835 0 R 3836 0 R 3837 0 R 3838 0 R
3839 0 R 3840 0 R 3841 0 R 3842 0 R 3843 0 R 3844 0 R 3845 0 R 3846 0 R 3847 0 R 3848 0 R
3849 0 R 3850 0 R 3851 0 R 3852 0 R 3853 0 R 3854 0 R]
 722 3855 0 R 723 3856 0 R 724 3857 0 R
725 [3858 0 R 3859 0 R 3860 0 R 3861 0 R 3862 0 R 3863 0 R 3864 0 R 3865 0 R 3866 0 R 3867 0 R
3868 0 R 3869 0 R 3870 0 R 3871 0 R 3872 0 R 3873 0 R 3874 0 R 3875 0 R 3876 0 R 3877 0 R
3878 0 R 3879 0 R 3880 0 R 3881 0 R 3882 0 R 3883 0 R 3884 0 R 3885 0 R 3886 0 R 3887 0 R
3888 0 R 3889 0 R 3890 0 R 3891 0 R 3892 0 R 3893 0 R 3894 0 R 3895 0 R 3896 0 R 3897 0 R
3898 0 R 3899 0 R 3900 0 R 3901 0 R 3902 0 R 3903 0 R 3904 0 R 3905 0 R 3906 0 R 3907 0 R
3908 0 R 3909 0 R 3910 0 R 3911 0 R 3912 0 R 3913 0 R 3914 0 R 3915 0 R 3916 0 R 3917 0 R
3918 0 R 3919 0 R 3920 0 R 3921 0 R 3922 0 R 3923 0 R 3924 0 R 3925 0 R]
 726 3926 0 R 727 [3927 0 R 3928 0 R 3929 0 R 3930 0 R 3931 0 R 3932 0 R 3933 0 R 3934 0 R 3935 0 R 3936 0 R
3937 0 R 3938 0 R 3939 0 R 3940 0 R 3941 0 R 3942 0 R 3943 0 R 3944 0 R 3945 0 R 3946 0 R
3947 0 R 3948 0 R 3949 0 R 3950 0 R 3951 0 R 3952 0 R 3953 0 R 3954 0 R 3955 0 R 3956 0 R
3957 0 R 3958 0 R 3959 0 R 3960 0 R 3961 0 R 3962 0 R 3963 0 R 3964 0 R 3965 0 R 3966 0 R
3967 0 R 3968 0 R 3969 0 R 3970 0 R 3971 0 R 3972 0 R 3973 0 R 3974 0 R 3975 0 R 3976 0 R
3977 0 R 3978 0 R 3979 0 R 3980 0 R 3981 0 R 3982 0 R 3983 0 R 3984 0 R 3985 0 R 3986 0 R
3987 0 R 3988 0 R 3989 0 R 3990 0 R 3991 0 R 3992 0 R 3993 0 R 3994 0 R 3995 0 R 3996 0 R
3997 0 R 3998 0 R 3999 0 R 4000 0 R 4001 0 R 4002 0 R 4003 0 R null 4004 0 R 4005 0 R
4006 0 R 4007 0 R 4008 0 R 4009 0 R null 4010 0 R 4011 0 R 4012 0 R 4013 0 R 4014 0 R
4015 0 R 4016 0 R 4017 0 R 4018 0 R 4019 0 R 4020 0 R 4021 0 R 4022 0 R 4023 0 R 4024 0 R
4025 0 R 4026 0 R 4027 0 R 4028 0 R 4029 0 R 4030 0 R 4031 0 R 4032 0 R 4033 0 R 4034 0 R
4035 0 R 4036 0 R 4037 0 R 4038 0 R 4039 0 R 4040 0 R 4041 0 R 4042 0 R 4043 0 R 4044 0 R
4045 0 R null]
 728 4046 0 R 729 [4047 0 R 4048 0 R 4049 0 R 4050 0 R 4051 0 R 4052 0 R 4053 0 R 4054 0 R 4055 0 R 4056 0 R
4057 0 R 4058 0 R 4059 0 R 4060 0 R 4061 0 R 4062 0 R 4063 0 R 4064 0 R 4065 0 R 4066 0 R
4067 0 R 4068 0 R 4069 0 R 4070 0 R 4071 0 R 4072 0 R 4073 0 R 4074 0 R 4075 0 R 4076 0 R
4077 0 R 4078 0 R 4079 0 R 4080 0 R 4081 0 R 4082 0 R 4083 0 R 4084 0 R 4085 0 R 4086 0 R
4087 0 R 4088 0 R 4089 0 R 4090 0 R 4091 0 R 4092 0 R 4093 0 R 4094 0 R 4095 0 R 4096 0 R
4097 0 R 4098 0 R 4099 0 R 4100 0 R 4101 0 R 4102 0 R 4103 0 R 4104 0 R 4105 0 R 4106 0 R
4107 0 R 4108 0 R 4109 0 R 4110 0 R 4111 0 R 4112 0 R 4113 0 R 4114 0 R 4115 0 R 4116 0 R
4117 0 R 4118 0 R 4119 0 R 4120 0 R 4121 0 R 4122 0 R 4123 0 R 4124 0 R 4125 0 R 4126 0 R
4127 0 R 4128 0 R 4129 0 R 4130 0 R 4131 0 R 4132 0 R 4133 0 R 4134 0 R 4135 0 R 4136 0 R
4137 0 R 4138 0 R 4139 0 R 4140 0 R 4141 0 R 4142 0 R 4143 0 R 4144 0 R 4145 0 R 4146 0 R
4147 0 R 4148 0 R 4149 0 R 4150 0 R 4151 0 R 4152 0 R 4153 0 R 4154 0 R 4155 0 R 4156 0 R
4157 0 R 4158 0 R 4159 0 R 4160 0 R 4161 0 R 4162 0 R 4163 0 R 4164 0 R 4165 0 R 4166 0 R
4167 0 R 4168 0 R 4169 0 R 4170 0 R 4171 0 R 4172 0 R 4173 0 R 4174 0 R 4175 0 R 4176 0 R
4177 0 R 4178 0 R 4179 0 R 4180 0 R 4181 0 R 4182 0 R 4183 0 R 4184 0 R 4185 0 R 4186 0 R
4187 0 R 4188 0 R 4189 0 R 4190 0 R 4191 0 R 4192 0 R 4193 0 R 4194 0 R 4195 0 R 4196 0 R
4197 0 R 4198 0 R 4199 0 R 4200 0 R 4201 0 R 4202 0 R 4203 0 R 4204 0 R 4205 0 R 4206 0 R
4207 0 R 4208 0 R 4209 0 R 4210 0 R 4211 0 R 4212 0 R 4213 0 R 4214 0 R 4215 0 R 4216 0 R
4217 0 R 4218 0 R 4219 0 R 4220 0 R 4221 0 R 4222 0 R 4223 0 R 4224 0 R 4225 0 R 4226 0 R
4227 0 R 4228 0 R 4229 0 R 4230 0 R 4231 0 R 4232 0 R 4233 0 R 4234 0 R 4235 0 R 4236 0 R
4237 0 R 4238 0 R 4239 0 R 4240 0 R 4241 0 R 4242 0 R 4243 0 R 4244 0 R 4245 0 R 4246 0 R
4247 0 R 4248 0 R 4249 0 R 4250 0 R 4251 0 R 4252 0 R 4253 0 R 4254 0 R 4255 0 R 4256 0 R
4257 0 R 4258 0 R 4259 0 R 4260 0 R 4261 0 R 4262 0 R 4263 0 R 4264 0 R 4265 0 R 4266 0 R
4267 0 R 4268 0 R 4269 0 R 4270 0 R 4271 0 R 4272 0 R 4273 0 R 4274 0 R 4275 0 R 4276 0 R
4277 0 R 4278 0 R 4279 0 R 4280 0 R 4281 0 R 4282 0 R 4283 0 R 4284 0 R 4285 0 R 4286 0 R
4287 0 R 4288 0 R 4289 0 R 4290 0 R 4291 0 R 4292 0 R 4293 0 R 4294 0 R 4295 0 R 4296 0 R
4297 0 R 4298 0 R 4299 0 R 4300 0 R 4301 0 R 4302 0 R 4303 0 R 4304 0 R 4305 0 R 4306 0 R
4307 0 R 4308 0 R 4309 0 R 4310 0 R 4311 0 R 4312 0 R 4313 0 R 4314 0 R 4315 0 R 4316 0 R
4317 0 R 4318 0 R 4319 0 R 4320 0 R 4321 0 R 4322 0 R 4323 0 R 4324 0 R 4325 0 R 4326 0 R
4327 0 R 4328 0 R 4329 0 R 4330 0 R 4331 0 R 4332 0 R 4333 0 R 4334 0 R 4335 0 R 4336 0 R
4337 0 R 4338 0 R 4339 0 R 4340 0 R 4341 0 R 4342 0 R 4343 0 R 4344 0 R 4345 0 R 4346 0 R
4347 0 R 4348 0 R 4349 0 R 4350 0 R 4351 0 R 4352 0 R 4353 0 R 4354 0 R 4355 0 R 4356 0 R
4357 0 R 4358 0 R 4359 0 R 4360 0 R 4361 0 R 4362 0 R 4363 0 R 4364 0 R 4365 0 R 4366 0 R
4367 0 R 4368 0 R 4369 0 R 4370 0 R 4371 0 R 4372 0 R 4373 0 R 4374 0 R 4375 0 R 4376 0 R
4377 0 R 4378 0 R 4379 0 R 4380 0 R 4381 0 R 4382 0 R 4383 0 R 4384 0 R 4385 0 R]
730 [4386 0 R 4387 0 R 4388 0 R 4389 0 R 4390 0 R 4391 0 R 4392 0 R 4393 0 R 4394 0 R 4395 0 R
4396 0 R 4397 0 R 4398 0 R 4399 0 R 4400 0 R 4401 0 R 4402 0 R 4403 0 R 4404 0 R 4405 0 R
4406 0 R 4407 0 R 4408 0 R 4409 0 R 4410 0 R 4411 0 R 4412 0 R 4413 0 R 4414 0 R 4415 0 R
4416 0 R 4417 0 R 4418 0 R 4419 0 R 4420 0 R 4421 0 R 4422 0 R 4423 0 R 4424 0 R 4425 0 R
4426 0 R 4427 0 R 4428 0 R 4429 0 R 4430 0 R 4431 0 R 4432 0 R 4433 0 R 4434 0 R 4435 0 R
4436 0 R 4437 0 R 4438 0 R 4439 0 R 4440 0 R 4441 0 R 4442 0 R 4443 0 R 4444 0 R 4445 0 R
4446 0 R 4447 0 R 4448 0 R 4449 0 R 4450 0 R 4451 0 R 4452 0 R 4453 0 R 4454 0 R 4455 0 R
4456 0 R 4457 0 R 4458 0 R 4459 0 R 4460 0 R 4461 0 R 4462 0 R 4463 0 R 4464 0 R 4465 0 R
4466 0 R 4467 0 R 4468 0 R 4469 0 R 4470 0 R 4471 0 R 4472 0 R 4473 0 R 4474 0 R 4475 0 R
4476 0 R 4477 0 R 4478 0 R 4479 0 R 4480 0 R 4481 0 R 4482 0 R 4483 0 R 4484 0 R 4485 0 R
4486 0 R 4487 0 R 4488 0 R 4489 0 R 4490 0 R 4491 0 R 4492 0 R 4493 0 R 4494 0 R 4495 0 R
4496 0 R 4497 0 R 4498 0 R 4499 0 R 4500 0 R 4501 0 R 4502 0 R 4503 0 R 4504 0 R 4505 0 R
4506 0 R 4507 0 R 4508 0 R 4509 0 R 4510 0 R 4511 0 R 4512 0 R 4513 0 R 4514 0 R 4515 0 R
4516 0 R 4517 0 R 4518 0 R 4519 0 R 4520 0 R 4521 0 R 4522 0 R 4523 0 R 4524 0 R 4525 0 R
4526 0 R 4527 0 R 4528 0 R 4529 0 R 4530 0 R 4531 0 R 4532 0 R 4533 0 R 4534 0 R 4535 0 R
4536 0 R 4537 0 R 4538 0 R 4539 0 R 4540 0 R 4541 0 R 4542 0 R 4543 0 R 4544 0 R 4545 0 R
4546 0 R 4547 0 R 4548 0 R 4549 0 R 4550 0 R 4551 0 R 4552 0 R 4553 0 R 4554 0 R 4555 0 R
4556 0 R 4557 0 R 4558 0 R 4559 0 R 4560 0 R 4561 0 R 4562 0 R 4563 0 R 4564 0 R 4565 0 R
4566 0 R 4567 0 R 4568 0 R 4569 0 R 4570 0 R 4571 0 R 4572 0 R 4573 0 R 4574 0 R 4575 0 R
4576 0 R 4577 0 R 4578 0 R 4579 0 R null 4580 0 R 4581 0 R 4582 0 R 4583 0 R 4584 0 R
4585 0 R null 4586 0 R 4587 0 R 4588 0 R 4589 0 R 4590 0 R 4591 0 R 4592 0 R 4593 0 R
4594 0 R 4595 0 R 4596 0 R 4597 0 R 4598 0 R 4599 0 R 4600 0 R 4601 0 R 4602 0 R 4603 0 R
4604 0 R 4605 0 R 4606 0 R 4607 0 R 4608 0 R 4609 0 R 4610 0 R 4611 0 R 4612 0 R 4613 0 R
4614 0 R 4615 0 R 4616 0 R 4617 0 R 4618 0 R 4619 0 R 4620 0 R 4621 0 R 4622 0 R 4623 0 R
4624 0 R null]
 731 4625 0 R 732 4626 0 R 733 4627 0 R 734 4627 0 R
735 [4628 0 R 4629 0 R 4630 0 R 4631 0 R 4632 0 R 4633 0 R 4634 0 R 4635 0 R 4636 0 R 4637 0 R
4638 0 R 4639 0 R 4640 0 R 4641 0 R 4642 0 R 4643 0 R 4644 0 R 4645 0 R 4646 0 R 4647 0 R
4648 0 R 4649 0 R 4650 0 R 4651 0 R 4652 0 R 4653 0 R 4654 0 R 4655 0 R 4656 0 R 4657 0 R
4658 0 R 4659 0 R 4660 0 R 4661 0 R 4662 0 R 4663 0 R 4664 0 R 4665 0 R 4666 0 R 4667 0 R
2358 0 R 2359 0 R 2360 0 R 2361 0 R 2362 0 R]
 736 4668 0 R 737 4668 0 R 738 [4669 0 R 4670 0 R 4671 0 R 4672 0 R 4673 0 R 4674 0 R 4675 0 R 4676 0 R 4677 0 R 4678 0 R
4679 0 R 4680 0 R 4681 0 R 4682 0 R 4683 0 R 4684 0 R 4685 0 R 4686 0 R 4687 0 R 4688 0 R
4689 0 R 4690 0 R 4691 0 R 4692 0 R 4693 0 R 4694 0 R 4695 0 R 4696 0 R 4697 0 R 4698 0 R
4699 0 R 4700 0 R 4701 0 R 4702 0 R 4703 0 R 4704 0 R 4705 0 R 4706 0 R 4707 0 R 4708 0 R
4709 0 R null 4710 0 R 4711 0 R 4712 0 R 4713 0 R 4714 0 R 4715 0 R null 4716 0 R
4717 0 R 4718 0 R 4719 0 R 4720 0 R 4721 0 R 4722 0 R 4723 0 R 4724 0 R 4725 0 R 4726 0 R
4727 0 R 4728 0 R 4729 0 R 4730 0 R 4731 0 R 4732 0 R 4733 0 R 4734 0 R 4735 0 R 4736 0 R
4737 0 R 4738 0 R 4739 0 R 4740 0 R 4741 0 R 4742 0 R 4743 0 R 4744 0 R 4745 0 R 4746 0 R
4747 0 R 4748 0 R 4749 0 R 4750 0 R 4751 0 R 4752 0 R 4753 0 R 4754 0 R 4755 0 R 4756 0 R
4757 0 R 4758 0 R 4759 0 R 4760 0 R 4761 0 R 4762 0 R 4763 0 R 4764 0 R 4765 0 R 4766 0 R
4767 0 R 4768 0 R 4769 0 R 4770 0 R 4771 0 R 4772 0 R 4773 0 R 4774 0 R 4775 0 R 4776 0 R
4777 0 R 4778 0 R 4779 0 R 4780 0 R 4781 0 R 4782 0 R 4783 0 R 4784 0 R 4785 0 R 4786 0 R
4787 0 R 4788 0 R null]
 739 4789 0 R
740 4790 0 R 741 4791 0 R 742 4792 0 R 743 4793 0 R 744 4794 0 R
745 [4795 0 R 4796 0 R 4797 0 R 4798 0 R 4799 0 R 4800 0 R 4801 0 R 4802 0 R 4803 0 R 4804 0 R
4805 0 R 4806 0 R 4807 0 R 4808 0 R 4809 0 R 4810 0 R 4811 0 R 4812 0 R 4813 0 R 4814 0 R
4815 0 R 4816 0 R 4817 0 R 4818 0 R 4819 0 R 4820 0 R 4821 0 R 4822 0 R 4823 0 R 4824 0 R
4825 0 R 4826 0 R 4827 0 R 4828 0 R 4829 0 R 4830 0 R 4831 0 R 4832 0 R 4833 0 R 4834 0 R
4835 0 R 4836 0 R 4837 0 R 4838 0 R 4839 0 R 4840 0 R 4841 0 R 4842 0 R 4843 0 R 4844 0 R
4845 0 R 4846 0 R 4847 0 R 4848 0 R 4849 0 R 4850 0 R null 4851 0 R 4852 0 R 4853 0 R
4854 0 R 4855 0 R 4856 0 R null 4857 0 R 4858 0 R 4859 0 R 4860 0 R 4861 0 R 4862 0 R
4863 0 R 4864 0 R 4865 0 R 4866 0 R 4867 0 R 4868 0 R 4869 0 R 4870 0 R 4871 0 R 4872 0 R
4873 0 R 4874 0 R 4875 0 R 4876 0 R 4877 0 R 4878 0 R 4879 0 R 4880 0 R 4881 0 R 4882 0 R
4883 0 R 4884 0 R 4885 0 R 4886 0 R 4887 0 R 4888 0 R 4889 0 R 4890 0 R 4891 0 R 4892 0 R
4893 0 R 4894 0 R 4895 0 R 4896 0 R 4897 0 R 4898 0 R 4899 0 R 4900 0 R 4901 0 R 4902 0 R
4903 0 R 4904 0 R 4905 0 R 4906 0 R 4907 0 R 4908 0 R 4909 0 R 4910 0 R 4911 0 R null
2363 0 R 2374 0 R 2364 0 R 2365 0 R]
 746 4912 0 R 747 [4913 0 R 4914 0 R 4915 0 R 4916 0 R 4917 0 R 4918 0 R 4919 0 R 4920 0 R 4921 0 R 4922 0 R
4923 0 R 4924 0 R 4925 0 R 4926 0 R 4927 0 R 4928 0 R 4929 0 R 4930 0 R 4931 0 R 4932 0 R
4933 0 R 4934 0 R 4935 0 R 4936 0 R 4937 0 R 4938 0 R 4939 0 R 4940 0 R 4941 0 R 4942 0 R
4943 0 R 4944 0 R 4945 0 R 4946 0 R 4947 0 R 4948 0 R 4949 0 R 4950 0 R 4951 0 R 4952 0 R
4953 0 R 4954 0 R 4955 0 R 4956 0 R 4957 0 R 4958 0 R 4959 0 R 4960 0 R 4961 0 R 4962 0 R
4963 0 R 4964 0 R 4965 0 R 4966 0 R 4967 0 R 4968 0 R 4969 0 R 4970 0 R 4971 0 R 4972 0 R
4973 0 R 4974 0 R 4975 0 R 4976 0 R 4977 0 R 4978 0 R 4979 0 R 4980 0 R 4981 0 R 4982 0 R
4983 0 R 4984 0 R 4985 0 R 4986 0 R 4987 0 R 4988 0 R 4989 0 R 4990 0 R 4991 0 R 4992 0 R
4993 0 R 4994 0 R 4995 0 R 4996 0 R 4997 0 R 4998 0 R 4999 0 R 5000 0 R 5001 0 R 5002 0 R
5003 0 R 5004 0 R 5005 0 R 5006 0 R 5007 0 R 5008 0 R 5009 0 R 5010 0 R 5011 0 R 5012 0 R
5013 0 R 5014 0 R 5015 0 R 5016 0 R 5017 0 R 5018 0 R 5019 0 R 5020 0 R 5021 0 R 5022 0 R
5023 0 R 5024 0 R 5025 0 R 5026 0 R 5027 0 R 5028 0 R 5029 0 R 5030 0 R 5031 0 R 5032 0 R
5033 0 R 5034 0 R 5035 0 R 5036 0 R 5037 0 R 5038 0 R 5039 0 R 5040 0 R 5041 0 R 5042 0 R
5043 0 R 5044 0 R 5045 0 R 5046 0 R 5047 0 R 5048 0 R 5049 0 R 5050 0 R 5051 0 R 5052 0 R
5053 0 R 5054 0 R 5055 0 R 5056 0 R 5057 0 R 5058 0 R 5059 0 R 5060 0 R 5061 0 R 5062 0 R
5063 0 R 5064 0 R 5065 0 R 5066 0 R 5067 0 R 5068 0 R 5069 0 R 5070 0 R 5071 0 R 5072 0 R
5073 0 R 5074 0 R 5075 0 R 5076 0 R 5077 0 R 5078 0 R 5079 0 R 5080 0 R 5081 0 R 5082 0 R
5083 0 R 5084 0 R 5085 0 R 5086 0 R 5087 0 R 5088 0 R 5089 0 R 5090 0 R 5091 0 R 5092 0 R
5093 0 R 5094 0 R 5095 0 R 5096 0 R 5097 0 R 5098 0 R 5099 0 R 5100 0 R 5101 0 R 5102 0 R
5103 0 R 5104 0 R 5105 0 R 5106 0 R 5107 0 R 5108 0 R 5109 0 R 5110 0 R 5111 0 R 5112 0 R
5113 0 R 5114 0 R 5115 0 R 5116 0 R 5117 0 R 5118 0 R 5119 0 R 5120 0 R 5121 0 R 5122 0 R
5123 0 R 5124 0 R 5125 0 R 5126 0 R 5127 0 R 5128 0 R 5129 0 R 5130 0 R 5131 0 R 5132 0 R
5133 0 R 5134 0 R 5135 0 R 5136 0 R 5137 0 R 5138 0 R 5139 0 R 5140 0 R 5141 0 R 5142 0 R
5143 0 R 5144 0 R 5145 0 R 5146 0 R 5147 0 R 5148 0 R 5149 0 R 5150 0 R 5151 0 R 5152 0 R
5153 0 R 5154 0 R 5155 0 R 5156 0 R 5157 0 R 5158 0 R 5159 0 R 5160 0 R 5161 0 R 5162 0 R
5163 0 R 5164 0 R 5165 0 R 5166 0 R 5167 0 R 5168 0 R 5169 0 R 5170 0 R 5171 0 R 5172 0 R
5173 0 R 5174 0 R 5175 0 R 5176 0 R 5177 0 R 5178 0 R 5179 0 R 5180 0 R 5181 0 R 5182 0 R
5183 0 R 5184 0 R 5185 0 R 5186 0 R 5187 0 R 5188 0 R 5189 0 R 5190 0 R 5191 0 R 5192 0 R
5193 0 R 5194 0 R 5195 0 R 5196 0 R 5197 0 R 5198 0 R 5199 0 R 5200 0 R 5201 0 R 5202 0 R
5203 0 R 5204 0 R 5205 0 R 5206 0 R 5207 0 R 5208 0 R 5209 0 R 5210 0 R 5211 0 R 5212 0 R
5213 0 R 5214 0 R 5215 0 R 2366 0 R 2367 0 R]
 748 5216 0 R 749 5217 0 R
750 5218 0 R 751 [3062 0 R 5219 0 R 5220 0 R 5221 0 R 5222 0 R 5223 0 R 5224 0 R 5225 0 R 5226 0 R 5227 0 R
5228 0 R 5229 0 R 5230 0 R 5231 0 R 5232 0 R 5233 0 R 5234 0 R 5235 0 R 5236 0 R 5237 0 R
5238 0 R 5239 0 R 5240 0 R 5241 0 R 5242 0 R 5243 0 R 5244 0 R 5245 0 R 5246 0 R 5247 0 R
5248 0 R 5249 0 R 5250 0 R 5251 0 R 5252 0 R 5253 0 R 5254 0 R 5255 0 R 5256 0 R 5257 0 R
5258 0 R 5259 0 R 5260 0 R 5261 0 R 5262 0 R 5263 0 R 5264 0 R 5265 0 R 5266 0 R 5267 0 R
5268 0 R 5269 0 R null 5270 0 R 5271 0 R 5272 0 R 5273 0 R 5274 0 R 5275 0 R null
5276 0 R 5277 0 R 5278 0 R 5279 0 R 5280 0 R 5281 0 R 5282 0 R 5283 0 R 5284 0 R 5285 0 R
5286 0 R 5287 0 R 5288 0 R 5289 0 R 5290 0 R 5291 0 R 5292 0 R 5293 0 R 5294 0 R 5295 0 R
5296 0 R 5297 0 R 5298 0 R 5299 0 R 5300 0 R 5301 0 R 5302 0 R 5303 0 R 5304 0 R 5305 0 R
5306 0 R 5307 0 R 5308 0 R 5309 0 R 5310 0 R 5311 0 R 5312 0 R 5313 0 R 5314 0 R 5315 0 R
5316 0 R 5317 0 R 5318 0 R 5319 0 R 5320 0 R 5321 0 R 5322 0 R 5323 0 R 5324 0 R 5325 0 R
5326 0 R 5327 0 R 5328 0 R 5329 0 R 5330 0 R 5331 0 R 5332 0 R null 2371 0 R 2368 0 R]
 752 5333 0 R 753 5334 0 R 754 [5335 0 R 5336 0 R 5337 0 R 5338 0 R 5339 0 R 5340 0 R 5341 0 R 5342 0 R 5343 0 R 5344 0 R
5345 0 R 5346 0 R 5347 0 R 5348 0 R 5349 0 R 5350 0 R 5351 0 R 5352 0 R 5353 0 R 5354 0 R
5355 0 R 5356 0 R 5357 0 R 5358 0 R 5359 0 R 5360 0 R 5361 0 R 5362 0 R 5363 0 R 5364 0 R
5365 0 R 5366 0 R 5367 0 R 5368 0 R 5369 0 R 5370 0 R 5371 0 R 5372 0 R 5373 0 R 5374 0 R
5375 0 R 5376 0 R 5377 0 R 5378 0 R 5379 0 R 5380 0 R 5381 0 R 5382 0 R 5383 0 R 5384 0 R
5385 0 R 5386 0 R 5387 0 R 5388 0 R 5389 0 R 5390 0 R 5391 0 R 5392 0 R 5393 0 R 5394 0 R
5395 0 R 5396 0 R 5397 0 R 5398 0 R 5399 0 R 5400 0 R 5401 0 R 5402 0 R 5403 0 R 5404 0 R
5405 0 R 5406 0 R 5407 0 R 5408 0 R 5409 0 R 5410 0 R 5411 0 R 5412 0 R 5413 0 R 5414 0 R
5415 0 R 5416 0 R 5417 0 R 5418 0 R 5419 0 R 5420 0 R 5421 0 R 5422 0 R 5423 0 R 5424 0 R
5425 0 R 5426 0 R 5427 0 R 5428 0 R 5429 0 R 5430 0 R 5431 0 R 5432 0 R 5433 0 R 5434 0 R
5435 0 R 5436 0 R 5437 0 R 5438 0 R 5439 0 R 5440 0 R 5441 0 R 5442 0 R 5443 0 R 5444 0 R
5445 0 R 5446 0 R 5447 0 R 5448 0 R 5449 0 R 5450 0 R 5451 0 R 5452 0 R 5453 0 R 5454 0 R
5455 0 R 5456 0 R 5457 0 R 5458 0 R 5459 0 R 5460 0 R 5461 0 R 5462 0 R 5463 0 R 5464 0 R
5465 0 R 5466 0 R 5467 0 R 5468 0 R 5469 0 R 5470 0 R 5471 0 R 5472 0 R 5473 0 R 5474 0 R
5475 0 R 5476 0 R 5477 0 R 5478 0 R 5479 0 R 5480 0 R 5481 0 R 5482 0 R 5483 0 R 5484 0 R
null 5485 0 R 5486 0 R 5487 0 R 5488 0 R 5489 0 R 5490 0 R null 5491 0 R 5492 0 R
5493 0 R 5494 0 R 5495 0 R 5496 0 R 5497 0 R 5498 0 R 5499 0 R 5500 0 R 5501 0 R 5502 0 R
5503 0 R 5504 0 R 5505 0 R 5506 0 R 5507 0 R 5508 0 R 5509 0 R 5510 0 R null 2369 0 R
2370 0 R]
755 5511 0 R 756 5512 0 R 757 5513 0 R 758 5513 0 R 759 [5514 0 R 5515 0 R 5516 0 R 5517 0 R 5518 0 R 5519 0 R 5520 0 R 5521 0 R 5522 0 R 5523 0 R
5524 0 R 5525 0 R 5526 0 R 5527 0 R 5528 0 R 5529 0 R 5530 0 R 5531 0 R 5532 0 R 5533 0 R
5534 0 R 5535 0 R 5536 0 R 5537 0 R 5538 0 R 5539 0 R 5540 0 R 5541 0 R 5542 0 R 5543 0 R
5544 0 R 5545 0 R 5546 0 R 5547 0 R 5548 0 R 5549 0 R 5550 0 R 5551 0 R 5552 0 R 5553 0 R
5554 0 R 5555 0 R 5556 0 R 5557 0 R 5558 0 R 5559 0 R 5560 0 R 5561 0 R 5562 0 R 5563 0 R
5564 0 R 5565 0 R 5566 0 R 5567 0 R 5568 0 R 5569 0 R 5570 0 R 5571 0 R 5572 0 R 5573 0 R
5574 0 R 5575 0 R 5576 0 R 5577 0 R 5578 0 R 5579 0 R 5580 0 R 5581 0 R 5582 0 R 5583 0 R
5584 0 R 5585 0 R 5586 0 R 5587 0 R 5588 0 R 5589 0 R 5590 0 R 5591 0 R 5592 0 R 5593 0 R
5594 0 R 5595 0 R 5596 0 R 5597 0 R 5598 0 R 5599 0 R 5600 0 R 5601 0 R 5602 0 R 5603 0 R
5604 0 R 5605 0 R 5606 0 R 5607 0 R 5608 0 R 5609 0 R 5610 0 R 5611 0 R 5612 0 R 5613 0 R
5614 0 R 5615 0 R 5616 0 R 5617 0 R 5618 0 R 5619 0 R 5620 0 R 5621 0 R 5622 0 R 5623 0 R
5624 0 R 5625 0 R 5626 0 R 5627 0 R 5628 0 R 5629 0 R 5630 0 R 5631 0 R 5632 0 R null
5633 0 R 5634 0 R 5635 0 R 5636 0 R 5637 0 R 5638 0 R null 5639 0 R 5640 0 R 5641 0 R
5642 0 R 5643 0 R 5644 0 R 5645 0 R 5646 0 R 5647 0 R 5648 0 R 5649 0 R 5650 0 R 5651 0 R
5652 0 R 5653 0 R 5654 0 R 5655 0 R 5656 0 R 5657 0 R 5658 0 R 5659 0 R 5660 0 R 5661 0 R
5662 0 R 5663 0 R 5664 0 R 5665 0 R 5666 0 R 5667 0 R 5668 0 R 5669 0 R 5670 0 R 5671 0 R
5672 0 R 5673 0 R 5674 0 R 5675 0 R 5676 0 R 5677 0 R 5678 0 R 5679 0 R null null
null 5680 0 R 5681 0 R 5682 0 R 5683 0 R 5684 0 R 5685 0 R 5686 0 R null null
null]
760 5687 0 R 761 5688 0 R 762 5688 0 R 763 5689 0 R 764 5690 0 R
765 5691 0 R 766 5692 0 R 767 [5693 0 R 5694 0 R 5695 0 R 5696 0 R 5697 0 R 5698 0 R 5699 0 R 5700 0 R 5701 0 R 5702 0 R
5703 0 R 5704 0 R 5705 0 R 5706 0 R 5707 0 R 5708 0 R 5709 0 R 5710 0 R 5711 0 R 5712 0 R
5713 0 R 5714 0 R 5715 0 R 5716 0 R 5717 0 R 5718 0 R 5719 0 R 5720 0 R 5721 0 R 5722 0 R
5723 0 R 5724 0 R 5725 0 R 5726 0 R 5727 0 R 5728 0 R 5729 0 R 5730 0 R 5731 0 R 5732 0 R
5733 0 R 5734 0 R 5735 0 R 5736 0 R 5737 0 R 5738 0 R 5739 0 R 5740 0 R 5741 0 R 5742 0 R
5743 0 R 5744 0 R 5745 0 R 5746 0 R]
 768 5747 0 R]
>>
"""

    l1 = b"""/Type /Pages /Kids [
    4 0 R
    26 0 R
    40 0 R
    46 0 R
    52 0 R
    58 0 R
    64 0 R
    70 0 R
    76 0 R
    82 0 R
    88 0 R
    94 0 R
    100 0 R
    110 0 R
    117 0 R
    125 0 R
    132 0 R
    138 0 R
    144 0 R
    150 0 R
    156 0 R
    164 0 R
    170 0 R
    176 0 R
    182 0 R
    189 0 R
    195 0 R
    201 0 R
    211 0 R
    224 0 R
    ] /Count 30
    >>"""

    # print(parse_dictionary(l1))

    # print(parse_arrayObjects(b' <D1314BD7F74849CDFA34B503910604A1>\n<D1314BD7F74849CDFA34B503910604A1> '))
    # arr = b"2 0 R"
    # # todo investigate bug
    # it = ObjectIter(arr)
    # next(it)
    # next(it)
    #
    # print(it.peek(3))
    # print(it.peek(3))
    # print(it.peek(3))
    # print(it.move_poiter(3))
    # print(it.peek(2))
    # print(it.peek(2))

    # print(parse_arrayObjects(arr))
    #
    t2 = b"""/R17
       17 0 R>>"""
    #
    print(parse_dictionary(t2))
    #     print(parse_numeric("",ObjectIter("587.78")))
    t3 = b"""/BaseFont/FWRCSR+CMMIB10/FontDescriptor 34 0 R/Type/Font
/FirstChar 78/LastChar 121/Widths[ 950 0
0 0 0 0 0 0 0 0 947 674 0 0 0 0 0 0
0 0 0 0 0 0 0 544 0 0 0 0 0 0 0 0
0 0 0 0 415 0 0 0 0 590]
/Encoding/WinAnsiEncoding/Subtype/Type1>>"""
    print(parse_dictionary(t3))
#
#     t4 = """/Type/Encoding/BaseEncoding/WinAnsiEncoding/Differences[
# 0/parenleftbig/parenrightbig
# 16/parenleftBig/parenrightBig/parenleftbigg/parenrightbigg
# 26/braceleftbigg
# 34/bracketleftBigg/bracketrightBigg
# 40/braceleftBigg/bracerightBigg
# 56/bracelefttp/bracerighttp/braceleftbt/bracerightbt/braceleftmid/bracerightmid/braceex
# 80/summationtext
# 88/summationdisplay
# 90/integraldisplay
# 104/bracketleftBig/bracketrightBig
# 110/braceleftBig/bracerightBig/radicalbig
# 122/bracehtipdownleft/bracehtipdownright/bracehtipupleft/bracehtipupright]>>"""
#
#     print(parse_dictionary(t4))
#
#     r3 = """<<
# /Font << /F32 4 0 R /F31 5 0 R /F50 6 0 R /F51 7 0 R /F35 8 0 R /F38 9 0 R /F33 10 0 R /F34 11 0 R >>
# /ProcSet [ /PDF /Text ]
# >>
# endobj"""
#
#     print(parse_stream(ObjectIter(r3)))
#
#     r5 = """<<
# /Title <feff0050006f0077006500720050006f0069006e0074002d0050007200e400730065006e0074006100740069006f006e>
# /Author (Schumacher, Hendrik-Lukas)
# /CreationDate (D:20200430160325+02'00')
# /ModDate (D:20200430160325+02'00')
# /Producer <feff004d006900630072006f0073006f0066007400ae00200050006f0077006500720050006f0069006e007400ae0020006600fc00720020004f006600660069006300650020003300360035>
# /Creator <feff004d006900630072006f0073006f0066007400ae00200050006f0077006500720050006f0069006e007400ae0020006600fc00720020004f006600660069006300650020003300360035>
# >>
# endobj"""
#     o = ObjectIter(r5)
#     # print(objectIdentifier(o))
#
#     t6 = """<<
# /Type /FontDescriptor
# /FontName /BCDEEE+Calibri
# /Flags 32
# /ItalicAngle 0
# /Ascent 750
# /Descent -250
# /CapHeight 750
# /AvgWidth 521
# /MaxWidth 1743
# /FontWeight 400
# /XHeight 250
# /StemV 52
# /FontBBox [ -503 -250 1240 750]
# /FontFile2 27 0 R
# >>
# endobj"""
#
#     o = ObjectIter(t6)
#
#     # print(objectIdentifier(o))
#
#     l1 = """/Type /Pages /Kids [
#     4 0 R
#     26 0 R
#     40 0 R
#     46 0 R
#     52 0 R
#     58 0 R
#     64 0 R
#     70 0 R
#     76 0 R
#     82 0 R
#     88 0 R
#     94 0 R
#     100 0 R
#     110 0 R
#     117 0 R
#     125 0 R
#     132 0 R
#     138 0 R
#     144 0 R
#     150 0 R
#     156 0 R
#     164 0 R
#     170 0 R
#     176 0 R
#     182 0 R
#     189 0 R
#     195 0 R
#     201 0 R
#     211 0 R
#     224 0 R
#     ] /Count 30
#     >>"""
#
#     # print(parse_dictionary(l1))
