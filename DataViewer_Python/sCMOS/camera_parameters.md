DataViewer Parameters
=====================
<!-- Created 11 Dec 2021 -->

Introduction
------------

The ADGenCam/DataViewer setup is based on a common EPICS interface for parameters that control cameras.  Much of the idea is to have the commands from EPICS always have the same format among different cameras for the same parameters.  This document is a collection of existing parameters found in the cameras in DataViewer.

Sydor Tucsen
------------

### Touch Generic Parameter

* ds2c_GetImageType
	* Returns the enum for the data type.  Possibly redundant since image retrieval gets the number, but possibly useful as a sanity check.
* Connected
	* Returns connected status as a number.
* NImages
	* Returns number of images.  Distinguished from number of frames
* NFrames
	* Returns number of frames.  Distinguished from number of frames
* Resolutions
	* Appears to return number of resolutions available.  Listed as "not really used"
* Resolution
	* Returns enum for resolution qua binning of sensor.
* Region
	* Returns ROI-enabled flag and ROI of image.  **AMALGAMATION**
* Model
	* Returns Model string.
* Temperature
	* Returns temperature as a double.
* Interframe
	* Returns interframe time.
* Exposure
	* Returns exposure time. 
* Gain
	* Returns integer gain derived from double gain, so probably not an enum.
* Mode
	* Returns an integer Gain Mode.  Possibly a candidate for renaming.
* Trigger
	* Returns an integer Trigger Mode.  Differs from pre-defined AreaDetector trigger mode, but overrides are possible.  Comments in code may be inaccurate here.
* PRNU
	* Returns PRNU status: 1 or 0.
* HFlip
	* Returns HFlip status: 1 or 0.  There is an AreaDetector variable for this.
* VFlip
	* Returns VFlip status: 1 or 0.  There is an AreaDetector variable for this.
* AccumulateMode
	* Returns Accumulate Mode Status: 1 or 0.
* InputTriggerEdge
	* Returns Input Trigger Edge Mode.
* OutputTrigger
	* Returns output trigger mode
* OutputEdge
	* Returns output trigger edge mode.  The interaction of this PV and OutputTrigger should be considered.
* *
	* Refresh all parameters.

### Set Generic Parameter

* Exposure
	* Sets exposure time.
* Interframe
	* Sets interframe time.
* actionConnect
	* Connects to camera.
* NFrames
	* Sets number of frames, not to be confused with number of images.
* Trigger
	* Sets trigger mode.
* Resolution
	* Sets resolution qua binning.  Casts string to float to int.
* Region
	* Sets ROI enable, dimension minima, and sizes.  An **AMALGAMATION**.
* CaptureMode
	* Sets capture mode by an enum.
* q2c_SetFileName
	* Sets capture mode to "save++".
* actionTrigger
	* Runs a software trigger/
* actionCapture
	* Runs an acquisition.
* DSNU
	* Sets Boolean DSNU mode.
* PRNU
	* Sets Boolean PRNU mode.
* VFlip
	* Sets Boolean VFlip mode.
* HFlip
	* Sets Boolean HFlip mode.
* InputTriggerEdge
	* Sets input trigger edge.  Currently based on a string value.  See OutputTriggerEdge
* OutputEdge
	* Sets output trigger edge.  Currently based on a string value.  Uses opposite numbers for edge type.
* OutputTrigger
	* Sets output trigger from an int.
* Mode
	* Sets gain mode by an enum and resets gain to 3.  This parameter is a contender for renaming.
* AccumulateMode
	* Sets Boolean accumulate mode.
* Gain
	* Sets gain according to an enum.  Value is int(floor(double)).

SpectroCCD
----------

### Touch Generic Command

* ds2c_GetImageType
	* Returns the enum for the data type.  Possibly redundant since image retrieval gets the number, but possibly useful as a sanity check.
* ds2c\_Apply\_Cor?
	* Retrieves corrections being applied.  Listed as should be added to all cameras.  Appears stubbed out so far.
* BeaconList
	* Sets boolean ByPassConnect to true.  "Sorry" in comment.
* NImages
	* Returns number of images.
* ShutterStatus
	* Gets status of shutter -- presumably open or closed
* Shutter
	* Gets shutter mode.  Room for Sydor standardization here -- open, closed, and auto are current options.  There may be others, and we may want to establish an enum.
* Trigger
	* Gets trigger mode.  There is again perhaps some room for a Sydor-wide standardization.
* IntegTime
	* Gets exposure time.  This is a candidate for renaming and combining with "Exposure", above.
* Video
	* Gets video mode status.  Not supported by Spectro daemon.  This is a candidate for incorporation into other acquisition PVs, or having a different name.
* AcquiresSinceReset
	* Gets number of acquires since a reset.  Important for older Spectros due to noise.  
* Size
	* Gets image size.  The Spectro command gets two dimensions.  Size is a candidate for **AMALGAMATED** handling, and standardized among multiple detectors.
* Temps
	* Gets one (or more?) temperatures from the Spectro camera.  Compare with Temperature for Tucsen.
* Connected
	* Reports if controller connected -- Boolean result.
* q2c_PopulateCommands
	* Internal for QML population.
* GetAcqStatus
	* Returns acquisition status.  Spectro result is an enum, and there is room for Sydor standardization.
* "*"
	* Does the query of all parameters

### Set Generic Param

* ds2c_UnitTesting
	* Runs unit tests
* SelectServer
	* Connects to a Spectro controller.  Given MMPAD architecture, this may be common among at least two systems.
* IntegTime
	* As above.  Compare with Exposure in Tucsen.
* Size
	* Image Size.  An **AMALGAMATION** of X and Y.  Probably standardizable among detectors.
* actionDisconnect
	* Disconnects from a camera.
* actionFlush
	* Flushes a socket.
* setRotation
	* Sets rotation enable and amount.  An **AMALGAMATION**.  May be more generally applicable as a correction shared among multiple cameras.
* setOverscanSubtration
	* Sets overscan subtration enable and dummied-out parameter.  An **AMALGAMATION**, although the second variable is ignored.  A correction, but somewhat Spectro-specific.
* setHotPixel
	* Sets hot pixel correction enable and (percentage?).  An **AMALGATION**.  A correction, with a somewhat specific application in Spectro, but possibly generalizable.
* setAssemble
	* Re-interlaces an image.  An **AMALGAMATION** with an ignored second paramter.  This algorithm is Spectro-specific, but compare with geocorrection for MMPAD.
* SendCommand
	* Sends a command.  Should perhaps be common among all cameras?
* SendCommandByName
	* Ibid.
* q2c_SetFilename
	* Sets saving filename.  Compare capitalization with "q2c_SetFileName" from Tucsen.
* DoInit
	* Runs the camera initialization sequence.  This may be a candidate to standardize among multiple cameras.
* DoReset
	* Runs the camera reset sequence.  This may be a candidate to standardize among mulitple cameras.
* ShutterMode 
	* Sets the shutter mode.  This command is called "Shutter" in the getter.  We should standardize this.
* TriggerMode
	* Sets the trigger mode.  Called "Trigger" in the getter.  Different trigger modes should be standardized Sydor-wide.
* VideoMode
	* Sets the video mode.  Called "Video" in the getter.

Sim Camera
----------

### Touch Generic Param

* ds2c_GetImageType
	* Returns an enum of the image type.  May be useful for a sanity check, since EPICS uses other metadaya.
* ds2c\_Apply\_Cor?
	* Returns status of corrections being applied.  Question mark may perhaps be omitted.
* MandleCenter
	* Returns an **AMALGAMATION** of the Mandlebrot center.
* MandleWindow
	* Returns the Mandlebrot Window
* NImages
	* Returns number of images.
* NFrames
	* Returns number of frames.
* Exposure
	* Returns presumably exposure time.  Called "IntegTime" elsewhere.
* Size
	* Returns and **AMALGAMATION** of image size.
* FastMode
	* Returns a Boolean of fast mode enable.  Contrast with "Video" for Spectro.
* CaptureMode
	* Returns a capture mode.  This value is essentially an enum.

### Set Generic Param

* ds2c_UnitTesting
	* Runs the unit tests.
* q2c_SetFileName
	* Sets filename and saving mode on.  Compare capitalization to "SetFilename" elsewhere.
* actionTrigger
	* Takes a foreground image.  Contrast with actionCapture for acquiring versus triggering.
* setRotation
	* Sets Rotation Enable and angle.  An **AMALGAMATION**.
* setGeoCorrect
	* Sets Geocorrection enable.  An **AMALGAMATION**, but the second argument is ignored.

Sydor MMPAD Camera
------------------

### Touch Generic Param

* ds2c_GetImageType
	* Returns an enum of image type.  May be useful as a sanity check for EPICS to compare to other metadata.
* ds2c\_Apply\_Cor?
	* Returns if certain corrections are being applied.  An **AMALGAMATION**.  The question mark may perhaps be a candidate for revision.
* NTriggers
	* Returns triggers per run.
* ds2c_GetFrameCount
	* Returns number of frames in run, for either foreground or background.  Format is very different from format used in EPICS, and may need splitting to foreground or background for generic EPICS handling.
* FramesPerTrigger
	* Returns number of frames per trigger.
* IntegTime
	* Returns integation time.  Called "Exposure" elsewhere.  We should at least consider units, although EPICS is unit-agnostic.
* InterTime
	* Returns interframe time.  Called "Interframe" in Tucsen.
* Trigger
	* Gets trigger mode
* SensorPower
	* Returns if sensor is on or off.
* Shutter
	* Returns if shutter is open.  Contrast with ShutterStatus and ShutterMode in Spectro.
* Connected
	* Returns if connected to server.
* LivePreview
	* Returns if live preview enabled.
* AlignmentMode
	* Returns if in alignment mode.  Compare with Fast Mode for Sim Camera and Video Mode for Spectro, the latter's intended purpose being alignment.
* ds2c_GetFrameNumber
	* Dummied out, but intended to retrieve current frame number.
* "*"
	* Gets all parameters.

### Set Generic Param

* ds2c_UnitTesting
	* Runs unit tests.
* actionConnect
	* Starts connection procedure?
* actionDisconnect
	* Disconnects camera?
* selectServer
	* Chooses camera from list.
* actionTrigger
	* Triggers the camera.  Compare with actionTrigger and actionCapture.
* q2c_PopulateSetTable
	* ?
* q2c_PopulateRunTable
	* Populates run table from a set name.
* q2c_SelectRunItem
	* A big **AMALGAMATION** that sets a view based on passed options.
* q2c_AllBufferAttributes
	* ?
* FrameNumber
	* Sets display frame?
* FetchVirtualFrame
	* An **AMALGAMATION** that displays a foreground or background frame.
* actionStartRun
	* Starts or arms a run.  Compare with actionCapture and actionTrigger above.
* actionStopRun
	* Stops a run.  Consider standardization with Tucsen the ability to click cancel on an untriggered run.
* LivePreview
	* Sets sampling mode on or off.
* Alignment Mode
	* Sets alignment mode on or off.  Compare with Video Mode for Spectro.
* NTriggers
	* Sets number of triggers per run
* IntegTime
	* Sets integration time.  Called "Exposure" in other projects.
* InterTime
	* Sets interframe time.  Tucsen calls this "Interframe".
* Trigger
	* Sets trigger mode.  Spectro calls this "TriggerMode".
* SensorPower
	* Sets sensor power on or off.
* Shutter
	* Sets shutter state (open or closed).  Contrast ShutterMode and ShutterStatus.

Sydor KECKPAD
-------------

* ds2c_GetImageType
	* Returns an enum of image type.  Likely useful for sanity checking image metadata.
* ds2c\_Apply\_Cor?
	* An **AMALGAMATION** that reports on status of image correction.
* NImages
	* Retrieves number of images to take.
* NFrames
	* Retrieves CAPSEL.  This may be a case where a different name is desired.
* SensorPower
	* Retrieves sensor power status.
* ImageNum
	* Retrieves the RxSetNumber.
* ShutterStatus
	* Returns if shutter is open or closed.  Compare "Shutter" and "ShutterMode".
* IntegTime
	* Reports an integration time.  There can be multiple times, so some special handling may be needed.  Also called "Exposure".
* InterTime
	* Reports an interframe time.  There can be multiple times, so some special handling may be needed.  ALso called "Interframe".
* Connected
	* Reports if connected to Keck daemon.
* TriggerType
	* Dummied-out.  Possibly compare "Trigger" and "TriggerMode".
* q2c_RefreshControlTab
	* Updates UI.  Compare "*"?

### Set Generic Param

* ds2c_UnitTesting
	* Runs unit tests.
* SelectServer
	* Connects to server given in IP address in argument.
* actionDisconnect
	* Disconnects from server
* actionRunScript
	* Runs the script specified in argument.
* actionTrigger
	* Completely dummied out and not recognized.  Compare with actionCapture.
* LivePreview
	* Dummied out.  Sets Live View mode.
* SendKeckCommand
	* Sends a command in argument to Keck.
* NImages
	* Completely dummied-out and not recognized.  References number of images being set elsewhere.
* NFrames
	* Cap selection, so a possible candidate for a different name.
* SensorPower
	* Turns head on or off.
* Shutter
	* Opens or closes the shutter.  Compare ShutterMode and ShutterStatus.
* IntegTime
	* Sets integration time.  Time appears to be the same for all frames. Called "Exposure" elsewhere.
* InterTime
	* Sets interframe time.  Time appears to be the same for all frames.  Called "Interframe" elsewhere.
* CinSel
	* ?
* ReadMode
	* Sets read mode.  No other details known by me.
* ExpMode
	* ?
* ReadDelay
	* Sets read delay.
* TrigDelay
	* Sets trigger delay.
* TriggerType
	* Sets trigger mode.  Compare "TrigMode","Trigger" and "TriggerMode" elsewhere.
* TrigMode
	* Sets a different trigger mode?  Compare "Trigger", "TriggerType", and "TriggerMode".
* TriggerSource
	* Specifies trigger source.
* TakeImage
	* Takes an image.  Compare "actionTrigger" and "actionCapture".
* UI_Interface_WaitCursor
	* ?
* CaptureMode
	* Sets capture mode, and disable saving.
* q2c_SetFileName
	* Sets save filename.  Compare "q2c_SetFilename" with different capitalization.
* ds2c_Init
	* Runs some initialization.
* <n>Integ
	* Sets integration time for a specified cap.
* <n>Inter
	* Sets interframe time for a specified cap.

