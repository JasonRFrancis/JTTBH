-- BBC Big Read Top 100 Books
-- Source: https://www.bbc.co.uk/arts/bigread/top100.shtml (via Wikipedia)
-- Imports all 100 books as 'want' status books.
-- Idempotent: skips titles already present for this user.
-- Run after 20260529_media_tracker.sql.

SET @user_id = (SELECT userID FROM `user` WHERE username = 'jason' LIMIT 1);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '4af1a3df-606a-44c8-a471-b067ccb49246', 'The Lord of the Rings', 'book', 'J. R. R. Tolkien', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Lord of the Rings' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '12d901ef-268b-403e-a439-2f70f9ff00be', 'Pride and Prejudice', 'book', 'Jane Austen', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Pride and Prejudice' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '39cb2210-2109-4f2c-af4c-83e40b6216b4', 'His Dark Materials', 'book', 'Philip Pullman', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'His Dark Materials' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, 'a3f85fd8-e023-4ec3-9b41-79dc2aff582a', 'The Hitchhiker''s Guide to the Galaxy', 'book', 'Douglas Adams', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Hitchhiker''s Guide to the Galaxy' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, 'c4151999-e2cb-492b-a57f-39c4266056ff', 'Harry Potter and the Goblet of Fire', 'book', 'J. K. Rowling', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Harry Potter and the Goblet of Fire' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '429af0b5-9fcc-43b7-bb53-2049f7d113df', 'To Kill a Mockingbird', 'book', 'Harper Lee', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'To Kill a Mockingbird' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '9cb29122-6f75-45a4-b3ce-4c32840aec7a', 'Winnie-the-Pooh', 'book', 'A. A. Milne', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Winnie-the-Pooh' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '381268da-9e6d-495a-ba6a-a02e19935e73', 'Nineteen Eighty-Four', 'book', 'George Orwell', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Nineteen Eighty-Four' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, 'b4383673-2574-4353-b62d-a820acde94ae', 'The Lion, the Witch and the Wardrobe', 'book', 'C. S. Lewis', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Lion, the Witch and the Wardrobe' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, 'be0b8014-8f60-4c12-b800-665435e89bab', 'Jane Eyre', 'book', 'Charlotte Brontë', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Jane Eyre' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, 'f0b07de7-2a7b-41d8-ba00-7b8a7b95deca', 'Catch-22', 'book', 'Joseph Heller', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Catch-22' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '25241a20-d500-4bc5-849a-0d1aec486fa4', 'Wuthering Heights', 'book', 'Emily Brontë', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Wuthering Heights' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, 'd0961034-1463-41fb-8184-c00aa2c59d00', 'Birdsong', 'book', 'Sebastian Faulks', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Birdsong' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, 'bc80e99e-fad2-4207-b641-5bedcb39ee17', 'Rebecca', 'book', 'Daphne du Maurier', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Rebecca' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '8000a471-34cd-4829-bf44-87a0ca87d0b0', 'The Catcher in the Rye', 'book', 'J. D. Salinger', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Catcher in the Rye' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '9b887d68-2292-4f45-93fc-520280181e92', 'The Wind in the Willows', 'book', 'Kenneth Grahame', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Wind in the Willows' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '0f2ad008-78c3-4e0b-bee3-c2a6e27aaa85', 'Great Expectations', 'book', 'Charles Dickens', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Great Expectations' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '51272fd7-3461-49ce-a402-e8559ff5f07b', 'Little Women', 'book', 'Louisa May Alcott', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Little Women' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '05a21579-cae7-47fd-8d8d-1876c415c546', 'Captain Corelli''s Mandolin', 'book', 'Louis de Bernières', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Captain Corelli''s Mandolin' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, 'fef90297-f2b2-426f-85a6-8cb921fd3da5', 'War and Peace', 'book', 'Leo Tolstoy', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'War and Peace' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '0f1e1b5b-3712-4ab7-b697-89b6d1111119', 'Gone with the Wind', 'book', 'Margaret Mitchell', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Gone with the Wind' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '640a2901-9abc-46d6-8cca-38993866cfb4', 'Harry Potter and the Philosopher''s Stone', 'book', 'J. K. Rowling', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Harry Potter and the Philosopher''s Stone' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '8be62b39-d214-41a3-834f-79c6f18c68ae', 'Harry Potter and the Chamber of Secrets', 'book', 'J. K. Rowling', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Harry Potter and the Chamber of Secrets' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, 'e1c2aba6-0bee-425d-b090-f50a363ec997', 'Harry Potter and the Prisoner of Azkaban', 'book', 'J. K. Rowling', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Harry Potter and the Prisoner of Azkaban' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '31a77007-1787-471d-8149-581bef98041e', 'The Hobbit', 'book', 'J. R. R. Tolkien', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Hobbit' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, 'a9f64c9e-3447-4934-8bab-769bb7ef9275', 'Tess of the d''Urbervilles', 'book', 'Thomas Hardy', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Tess of the d''Urbervilles' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '6c6644e2-c6a0-4074-9403-d3ebc1d7acb2', 'Middlemarch', 'book', 'George Eliot', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Middlemarch' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, 'c1f6dda9-2132-4b9a-aae8-074a57036286', 'A Prayer for Owen Meany', 'book', 'John Irving', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'A Prayer for Owen Meany' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '3be816da-dab2-460f-af6e-57207a023a6f', 'The Grapes of Wrath', 'book', 'John Steinbeck', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Grapes of Wrath' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '9eb2c97e-b84f-4682-b80c-dd17ce860a48', 'Alice''s Adventures in Wonderland', 'book', 'Lewis Carroll', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Alice''s Adventures in Wonderland' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, 'fa0ce62a-18c9-43cd-8d87-f66217253554', 'The Story of Tracy Beaker', 'book', 'Jacqueline Wilson', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Story of Tracy Beaker' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '4f67adc5-b984-4fb8-b181-d9ec2fb1317c', 'One Hundred Years of Solitude', 'book', 'Gabriel García Márquez', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'One Hundred Years of Solitude' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '05e1455c-9de1-4636-8510-1018a3e52a54', 'The Pillars of the Earth', 'book', 'Ken Follett', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Pillars of the Earth' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, 'b59e65c9-1e2b-4b99-b077-015ecd303d45', 'David Copperfield', 'book', 'Charles Dickens', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'David Copperfield' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '2780c04c-efe0-4332-870d-1984dab7df21', 'Charlie and the Chocolate Factory', 'book', 'Roald Dahl', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Charlie and the Chocolate Factory' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '7e308c1c-0b89-4c2f-a008-91cd5bc8e9b6', 'Treasure Island', 'book', 'Robert Louis Stevenson', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Treasure Island' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, 'ae2e1ad6-0df1-4189-b053-e16bfa995b72', 'A Town Like Alice', 'book', 'Nevil Shute', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'A Town Like Alice' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, 'f8b2e6b0-cff3-43d7-b855-e51eb045ec8a', 'Persuasion', 'book', 'Jane Austen', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Persuasion' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '9675f2fb-a3c3-4148-a9f9-1cd28a653bd0', 'Dune', 'book', 'Frank Herbert', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Dune' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '0df17907-fe7b-4d8b-bbff-7b95bb1143ab', 'Emma', 'book', 'Jane Austen', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Emma' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, 'b66ffe43-2c24-47b8-b002-d85b8de36869', 'Anne of Green Gables', 'book', 'Lucy Maud Montgomery', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Anne of Green Gables' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, 'c12638d6-4160-4fee-9dc1-59d45c6f0973', 'Watership Down', 'book', 'Richard Adams', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Watership Down' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '77c04841-a216-4846-9917-bb8ce86e628e', 'The Great Gatsby', 'book', 'F. Scott Fitzgerald', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Great Gatsby' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '80f05c41-3ff6-4897-98f4-61a334bb934c', 'The Count of Monte Cristo', 'book', 'Alexandre Dumas', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Count of Monte Cristo' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '61c5f848-43ef-458d-8f44-9d864b41b3dc', 'Brideshead Revisited', 'book', 'Evelyn Waugh', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Brideshead Revisited' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '96940ebf-38c2-4c57-8699-3cf1b2e9abd3', 'Animal Farm', 'book', 'George Orwell', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Animal Farm' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '6333bf26-b6e9-4089-a682-4f27ba93567b', 'A Christmas Carol', 'book', 'Charles Dickens', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'A Christmas Carol' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '182e4efc-7f50-487b-9ada-5121564229a4', 'Far from the Madding Crowd', 'book', 'Thomas Hardy', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Far from the Madding Crowd' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '36f60a32-dee1-4d49-8310-da6b89792d89', 'Goodnight Mister Tom', 'book', 'Michelle Magorian', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Goodnight Mister Tom' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '5d9fd76d-19bb-42bd-a053-89d1bdeba1df', 'The Shell Seekers', 'book', 'Rosamunde Pilcher', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Shell Seekers' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '9e23cae7-c5ec-4175-8af5-f1ad5e62dd2b', 'The Secret Garden', 'book', 'Frances Hodgson Burnett', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Secret Garden' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, 'b83f0749-c820-4190-932d-b178c3d1f6da', 'Of Mice and Men', 'book', 'John Steinbeck', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Of Mice and Men' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, 'f2900764-0a37-4c8f-82ba-fa7e427632cd', 'The Stand', 'book', 'Stephen King', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Stand' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '64cd7b03-1b85-446a-85f5-2ec8643df190', 'Anna Karenina', 'book', 'Leo Tolstoy', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Anna Karenina' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '010777f6-df56-4531-afef-afdfa8080723', 'A Suitable Boy', 'book', 'Vikram Seth', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'A Suitable Boy' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '08937337-e480-4c0c-a0a1-1c3bdd25f5ff', 'The BFG', 'book', 'Roald Dahl', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The BFG' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '37c91bfe-0695-48c2-8089-9b030c150ed1', 'Swallows and Amazons', 'book', 'Arthur Ransome', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Swallows and Amazons' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '9ca98d07-3819-4c2f-903c-398f9eb980f3', 'Black Beauty', 'book', 'Anna Sewell', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Black Beauty' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '5b010a89-a1d6-42e7-8f1e-4b0d190bb153', 'Artemis Fowl', 'book', 'Eoin Colfer', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Artemis Fowl' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, 'e2c988a1-84e1-4cca-bf31-7e10ad1496ad', 'Crime and Punishment', 'book', 'Fyodor Dostoyevsky', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Crime and Punishment' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, 'f14470f9-7ffc-41c7-a172-efbc20c4b527', 'Noughts & Crosses', 'book', 'Malorie Blackman', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Noughts & Crosses' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '8ae52a84-5482-4d89-aecb-b5379816e890', 'Memoirs of a Geisha', 'book', 'Arthur Golden', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Memoirs of a Geisha' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '4b5ba6e9-2612-4a77-988d-1637a6be8b23', 'A Tale of Two Cities', 'book', 'Charles Dickens', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'A Tale of Two Cities' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '44d33842-226f-4b23-bbcd-b5725ed695eb', 'The Thorn Birds', 'book', 'Colleen McCullough', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Thorn Birds' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '1ded3017-86dd-41fc-8612-441a59f3340c', 'Mort', 'book', 'Terry Pratchett', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Mort' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '09a2c89a-5b18-4369-9fd7-032d8b028b08', 'The Magic Faraway Tree', 'book', 'Enid Blyton', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Magic Faraway Tree' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '842287a1-0b16-419e-be82-5ec1b6d5bc37', 'The Magus', 'book', 'John Fowles', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Magus' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '1ec2ca70-5d0d-43d4-bada-afd3c5b70f1e', 'Good Omens', 'book', 'Neil Gaiman and Terry Pratchett', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Good Omens' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, 'a637c7e2-563a-406f-90f4-79c1247e13ff', 'Guards! Guards!', 'book', 'Terry Pratchett', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Guards! Guards!' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '66612a7f-1c66-4372-b2d8-86723ab67e8d', 'Lord of the Flies', 'book', 'William Golding', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Lord of the Flies' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, 'f2062142-b9cc-4ad2-b806-0bd0a4b58358', 'Perfume', 'book', 'Patrick Süskind', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Perfume' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '1046a05a-3614-439d-90d7-b7ef7ff6035a', 'The Ragged-Trousered Philanthropists', 'book', 'Robert Tressell', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Ragged-Trousered Philanthropists' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '3e59f518-ab05-4bb7-bb87-223966dc64c0', 'Night Watch', 'book', 'Terry Pratchett', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Night Watch' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '67c58106-5299-4b71-8833-bb3f81a9e9e6', 'Matilda', 'book', 'Roald Dahl', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Matilda' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, 'e64833da-c7a2-4aa0-a4e7-11b33dc6fd66', 'Bridget Jones''s Diary', 'book', 'Helen Fielding', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Bridget Jones''s Diary' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, 'c63dbfc3-204b-4a29-ada5-1b81331cb37a', 'The Secret History', 'book', 'Donna Tartt', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Secret History' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '8209f0a2-5985-4790-b199-f04f0b2fb4a4', 'The Woman in White', 'book', 'Wilkie Collins', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Woman in White' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, 'da55a497-e205-4d8b-b509-08313e217f57', 'Ulysses', 'book', 'James Joyce', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Ulysses' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, 'b399bdf8-2f80-4ad1-8ead-76e683c4a8a0', 'Bleak House', 'book', 'Charles Dickens', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Bleak House' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '60e4d2a8-7a7b-4c4c-90bb-a3911b35c02d', 'Double Act', 'book', 'Jacqueline Wilson', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Double Act' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, 'd49f233f-324e-4183-9272-0c01eee811d4', 'The Twits', 'book', 'Roald Dahl', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Twits' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '6ade0dd9-2ce7-49d2-a10d-67486a6a7356', 'I Capture the Castle', 'book', 'Dodie Smith', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'I Capture the Castle' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '255bd021-f08e-48d0-8493-a8021c87c5b9', 'Holes', 'book', 'Louis Sachar', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Holes' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '932325a9-f2df-4bc9-bf42-a50c1d27f71e', 'Gormenghast', 'book', 'Mervyn Peake', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Gormenghast' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, 'aa7b3695-c6a8-42c2-972c-a60f187a69bb', 'The God of Small Things', 'book', 'Arundhati Roy', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The God of Small Things' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, 'a27e8548-cdd4-4109-9512-b1d0347d00ac', 'Vicky Angel', 'book', 'Jacqueline Wilson', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Vicky Angel' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, 'fa28d483-7515-4c1f-94df-37a661b9a0ee', 'Brave New World', 'book', 'Aldous Huxley', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Brave New World' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, 'f9ac3e19-ba4a-4c27-be45-baeee40ec59f', 'Cold Comfort Farm', 'book', 'Stella Gibbons', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Cold Comfort Farm' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '4358e594-cfc6-41da-b4a3-8b3fe9d3fdc6', 'Magician', 'book', 'Raymond E. Feist', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Magician' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, 'd9534867-4bc1-46cf-9510-9882f3319b6e', 'On the Road', 'book', 'Jack Kerouac', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'On the Road' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '25e04129-7d5a-4b15-9368-fece6466dc57', 'The Godfather', 'book', 'Mario Puzo', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Godfather' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '48921dd5-786e-4841-b7c9-3ca5ceb19b27', 'The Clan of the Cave Bear', 'book', 'Jean M. Auel', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Clan of the Cave Bear' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '90c2a538-bd4b-44c7-b7e7-a4e3368a4449', 'The Colour of Magic', 'book', 'Terry Pratchett', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Colour of Magic' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '8d16ff14-8596-4516-9da2-07a7d4661446', 'The Alchemist', 'book', 'Paulo Coelho', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Alchemist' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '8ac3c12d-34cd-4daa-8184-b940f40821d3', 'Katherine', 'book', 'Anya Seton', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Katherine' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, 'fd133f1c-1d45-450d-b24a-be6ac983a12b', 'Kane and Abel', 'book', 'Jeffrey Archer', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Kane and Abel' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '45740be3-4af3-46f7-82bf-943e995e5b33', 'Love in the Time of Cholera', 'book', 'Gabriel García Márquez', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Love in the Time of Cholera' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, 'a50d028c-28d3-480c-8010-85b2e5600e15', 'Girls in Love', 'book', 'Jacqueline Wilson', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Girls in Love' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '79cccd21-db12-4063-a7d4-7f614dd26760', 'The Princess Diaries', 'book', 'Meg Cabot', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Princess Diaries' AND kind = 'book' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, creator, status, created, created_by)
  SELECT @user_id, '70354394-c56b-4f4e-9424-719fa645273a', 'Midnight''s Children', 'book', 'Salman Rushdie', 'want', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Midnight''s Children' AND kind = 'book' AND title IS NOT NULL);
