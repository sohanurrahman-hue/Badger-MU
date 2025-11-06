import { z } from "zod";
import { IdentifierType, type Prisma } from "@prisma/client";

import { createTRPCRouter, protectedProcedure } from "../trpc";
import { CreateAwardSchema } from "../schemas/award.schema";
import {
  protectedAchievementCredentialInclude,
  publicAchievementCredentialSelect,
  publicAchievementSubjectSelect,
  // publicAchievementCredentialStatusSelect,
} from "~/server/db/queries";
import { env } from "~/env.mjs";
import { mongoDbObjectId } from "../schemas/util.schema";
import { URL } from "url";
// import { addCredentialStatus } from "../network-functions/add-credential-status";

type responseType = {
  recipientEmail: string;
  recipientName: string;
  awardName: string;
  awardUrl: string;
  issuerName: string;
};

// Helper function to try and get a filename from a URL
const getFilenameFromUrl = (url: URL): string => {
  try {
    const pathname = url.pathname;
    const parts = pathname.split('/');
    // Use the last part of the URL path as a filename, or default
    return parts[parts.length - 1] || "badge.png";
  } catch (e) {
    return "badge.png";
  }
};

// Calling the microservice to send award email
const sendAwardEmail = async (
      email: string, 
      name: String, 
      awardName: String, 
      credentialId: string, 
      issuerName: string, 
      awardUrl: String | null, 
      ImageUrl: URL | null )
      : Promise<responseType> => 
      {
        const emailServiceUrl = env.EMAIL_SERVICE_URL;
        console.log("Email Service URL:", emailServiceUrl);

        const payload = new FormData();
        payload.append("email", email);
        payload.append("body",  `Congratulations ${name}, you have been awarded the "${awardName}" credential ${credentialId}! You can view your award here: ${awardUrl}. And it was issued by ${issuerName}.`);
        payload.append("subject", `You've been awarded the "${awardName}" credential!`);

        // Get image filename for logging
        if (ImageUrl) {
          try {
            // Fetch the image from its URL
            const imageResponse = await fetch(ImageUrl.toString());
            
            if (imageResponse.ok) {
              const imageBlob = await imageResponse.blob();
              const filename = getFilenameFromUrl(ImageUrl);
              
              // The key MUST be "file" to match the 'UploadFile = File(None)' argument
              payload.append("file", imageBlob, filename);
            } else {
              console.warn(`Failed to fetch image for attachment: ${imageResponse.statusText}`);
            }
          } catch (error) {
            console.error("Error fetching attachment image:", error);
            // We can continue without the attachment
          }
        }

        const response = await fetch(emailServiceUrl, {
          method: "POST",
          body: payload,
        });

        if (!response.ok) {
          throw new Error(`Failed to send award email: ${response.statusText}`);
        }

        const data = await response.json();
        console.log("Award email sent successfully:", data);
        return data;

 };



export const awardRouter = createTRPCRouter({
  // Finds a credential by id, includes credentialStatus
  find: protectedProcedure
    .input(mongoDbObjectId)
    .query(async ({ ctx, input }) => {
      return ctx.prismaConnect.achievementCredential.findUniqueOrThrow({
        where: { docId: input },
        include: protectedAchievementCredentialInclude,
      });
    }),

  // New Delete Mutation
  delete: protectedProcedure
    .input(mongoDbObjectId)
    .mutation(async ({ ctx, input }) => {
      return ctx.prismaConnect.achievementCredential.deleteMany({
        where: { docId: input },
      });
    }),

  // returns a list of awarded credentials by ID
  index: protectedProcedure
    .input(
      z.object({
        credentialId: mongoDbObjectId,
        query: z.string(),
      }),
    )
    .query(async ({ ctx, input }) => {
      return ctx.prismaConnect.achievementCredential.findMany({
        include: {
          credentialStatus: true,
          credentialSubject: {
            include: {
              profile: true,
            },
          },
        },
        where: {
          credentialSubject: {
            achievementId: input.credentialId,
            ...(input.query
              ? {
                  profile: {
                    OR: ["name", "familyName", "givenName", "email"].map(
                      (f) => ({
                        [f]: { contains: input.query, mode: "insensitive" },
                      }),
                    ),
                  },
                }
              : {}),
          },
        },
        take: 10,
        orderBy: {
          awardedDate: "desc",
        },
      });
    }),

  // Creates a new achievementCredential for the specified learner Profile
  create: protectedProcedure
    .input(CreateAwardSchema)
    .mutation(async ({ ctx, input }) => {
      console.log("DEBUG: Input from frontend:", JSON.stringify(input, null, 2));
      const { credentialId, identifier, profile } = input;

      return ctx.prismaConnect.$transaction(async (prisma) => {
        const credential = await prisma.achievement.findUniqueOrThrow({
          where: { docId: credentialId },
          select: {
            docId: true,
            creatorId: true,
            name: true,
            description: true,
            image: { select: { docId: true }},
          },
        });

        const identityObject = await prisma.identityObject.create({
          data: {
            type: "IdentityObject",
            identityHash: identifier,
            identityType: IdentifierType.emailAddress,
            hashed: false,
          },
          select: { id: true },
        });

        const awardSubject: Prisma.AchievementSubjectCreateInput = {
          identifier: { connect: { id: identityObject.id } },
          achievement: { connect: { docId: credential.docId } },
          type: ["AchievementSubject"],
          source: { connect: { docId: credential.creatorId! } },
          profile: {
            create: {
              ...profile,
              email: identifier,
            },
          },
        };

        const awardee = await prisma.achievementSubject.create({
          data: awardSubject,
        });

        const awardedCredential: Prisma.AchievementCredentialCreateInput = {
          name: credential.name,
          type: ["AchievementCredential"],
          description: credential.description,
          id: awardee.docId, // Temporarily assign URI until a database ID is available.
          awardedDate: new Date().toISOString(),
          validFrom: new Date().toISOString(),
          credentialSubject: { connect: { docId: awardee.docId } },
          issuer: { connect: { docId: credential.creatorId! } },
          // If the achievement has an image, connect it to this new credential
          ...(credential.image && { image: { connect: { docId: credential.image.docId } } }),
        };

        const { docId } = await prisma.achievementCredential.create({
          data: awardedCredential,
          select: { docId: true },
        });

          // Prepare data for email microservice
        const updatedAwardedCredential = await prisma.achievementCredential.update({
            where: { docId },
            data: {
              id: `${env.NEXTAUTH_URL.replace(/\/$/, "")}/awards/${docId}`,
            },
            select: {
              ...publicAchievementCredentialSelect,
              image: {select:
                       {id: true,}},
              credentialSubject: {
                select: {
                  ...publicAchievementSubjectSelect,
                  profile: true,
                },
              },
              issuer: {
                select: {
                  name: true,
                },
              },
            },
          });

        console.log("DEBUG: Data for email:", JSON.stringify(updatedAwardedCredential, null, 2));
        // Send award email
        try {
          if (updatedAwardedCredential.credentialSubject?.profile) {
            // Get the base URL (make sure it doesn't have a trailing slash)
              const baseUrl = env.NEXTAUTH_URL.replace(/\/$/, ""); 

              // Create a full URL by combining the base URL and the image path
              const imageUrl = updatedAwardedCredential.image?.id
                ? new URL(updatedAwardedCredential.image.id, baseUrl)
                : null;
              // Add this log to see what URL is being created:
console.log("[next:dev] DEBUG: Created image URL to fetch:", imageUrl ? imageUrl.toString() : "null");
            await sendAwardEmail(
              identifier,
              updatedAwardedCredential.credentialSubject.profile.name || "Learner",
              updatedAwardedCredential.name,
              updatedAwardedCredential.id,
              updatedAwardedCredential.issuer.name || "Issuer",
              updatedAwardedCredential.id,
              imageUrl
            );
          }
        } catch (error) {
          console.error("Failed to send award email:", error);
          // Do not rethrow, as we don't want to fail the transaction if email sending fails
        }

        return updatedAwardedCredential;

  // NEW DELETE MUTATION
  

        // const awardedCredentialWithStatus = await addCredentialStatus(
        //   awardedCredentialWithId,
        // );

        // console.log("Cred with status:", awardedCredentialWithStatus);

        // return prisma.achievementCredential.update({
        //   where: { docId },
        //   data: {
        //     credentialStatus: {
        //       id: awardedCredentialWithStatus.docId,
        //       type: awardedCredentialWithStatus._type,
        //     },
        //   },
        //   select: publicAchievementCredentialStatusSelect,
        // });
      });
    }),
});
